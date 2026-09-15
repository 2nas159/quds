#!/usr/bin/env python3
"""
Visual quality gate.

Two halves, deliberately:

1. `inspect()` measures the ACTUAL rendered PNG. These checks are deterministic
   and catch exactly the defects that shipped before — a blank band across the
   top of a generated background, a logo composited so low-contrast it is
   invisible, elements colliding, a headline that vanishes at thumbnail size.
   No model judgement involved; they either fire or they don't.

2. `score()` merges those measurements with the reviewer's structured findings
   (the half that needs eyes on the image) into one rubric score and one
   decision, and routes each problem to the stage that can actually fix it.

The routing is the point. A photography defect costs an image-generation call
to fix; a layout defect costs a re-composite. Sending a layout problem back to
the image model is how the old loop burned credits without improving anything.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
from PIL import Image

from design_spec import Box, validate_layout

# --------------------------------------------------------------------------
# Rubric
# --------------------------------------------------------------------------

RUBRIC = {
    "composition": 25,
    "product_prominence": 20,
    "brand_consistency": 20,
    "typography_layout": 15,
    "photography_realism": 10,
    "cta_hierarchy": 5,
    "scroll_stopping": 5,
}
assert sum(RUBRIC.values()) == 100

PASS_EXCELLENT = 90
PASS_THRESHOLD = 85
REVISE_THRESHOLD = 75
MAX_REVISIONS = 2

# Which pipeline stage owns each problem category. This is what stops a badly
# placed label from triggering a fresh (paid) image generation.
FAILURE_ROUTES = {
    "photography": "regenerate_image",
    "realism": "regenerate_image",
    "lighting": "regenerate_image",
    "subject_framing": "regenerate_image",
    "composition": "revise_spec",
    "hierarchy": "revise_spec",
    "product_prominence": "revise_spec",
    "collision": "recomposite",
    "typography": "recomposite",
    "rendering": "recomposite",
    "proportion": "recomposite",
    "safe_area": "recomposite",
    "brand_consistency": "recomposite",
    "legibility": "recomposite",
}

ROUTE_ORDER = ["regenerate_image", "revise_spec", "recomposite"]

# Fraction of a rubric category a problem of each severity costs. "high" zeroes
# its category outright: a defect a viewer would actually notice does not earn
# partial credit in the area it ruins.
SEVERITY_WEIGHT = {"high": 1.0, "medium": 0.55, "low": 0.25}

# Arithmetic alone is too forgiving. A flat white band across the top of the
# frame only touches one rubric category, so it scored 95/100 and "passed" —
# which is how the broken render shipped. A high-severity defect is
# ship-blocking by definition, so it caps the decision regardless of the total.
HIGH_SEVERITY_REJECT_COUNT = 3

# Which rubric category each problem category deducts from.
CATEGORY_TO_RUBRIC = {
    "photography": "photography_realism",
    "realism": "photography_realism",
    "lighting": "photography_realism",
    "subject_framing": "composition",
    "composition": "composition",
    "collision": "composition",
    "safe_area": "composition",
    "hierarchy": "product_prominence",
    "product_prominence": "product_prominence",
    "proportion": "typography_layout",
    "typography": "typography_layout",
    "rendering": "typography_layout",
    "legibility": "typography_layout",
    "brand_consistency": "brand_consistency",
    "cta": "cta_hierarchy",
    "cta_hierarchy": "cta_hierarchy",
    "scroll_stopping": "scroll_stopping",
}


@dataclass
class Problem:
    category: str
    severity: str  # high | medium | low
    issue: str
    correction: str
    source: str = "automated"  # automated | reviewer
    element: str = ""
    # Explicit stage override. Some categories are genuinely ambiguous about
    # which stage owns them — "brand_consistency" covers both a wrong brand red
    # (a compositor fix) and wrong-coloured gloves (only an image regeneration
    # can fix that). Without this, a photography defect filed under
    # brand_consistency routes to the compositor and its correction is dropped
    # from the regeneration that actually needed it.
    stage: str = ""

    @property
    def route(self) -> str:
        if self.stage in ROUTE_ORDER:
            return self.stage
        return FAILURE_ROUTES.get(self.category, "revise_spec")

    def to_dict(self) -> dict:
        d = asdict(self)
        d["route"] = self.route
        return d


# --------------------------------------------------------------------------
# Automated measurement
# --------------------------------------------------------------------------

# A band is "dead" if its rows vary this little internally — a flat white or
# flat black strip left by a letterboxed or padded generation.
DEAD_BAND_ROW_STD = 6.0
DEAD_BAND_SPAN = 12.0
# Padding is colourless; a brand banner is not. This separates the two.
DEAD_BAND_MAX_CHROMA = 18.0
DEAD_BAND_MIN_FRACTION = 0.025
# Fraction of the frame that may be flat graphic fill before the creative stops
# reading as full-bleed photography.
GRAPHIC_COVERAGE_WARN = 0.20
GRAPHIC_COVERAGE_HIGH = 0.28
# Below this RMS difference from the underlying background, a composited
# element is effectively not there.
MIN_ELEMENT_CONTRAST = 12.0
# At thumbnail size an element needs at least this much local detail to read.
MIN_THUMBNAIL_DETAIL = 6.0
THUMBNAIL_WIDTH = 150


def _gray(img: Image.Image) -> np.ndarray:
    return np.asarray(img.convert("L"), dtype=np.float32)


def _runs(flags: np.ndarray):
    """Yield (start, length) for each run of True in a boolean array."""
    start = None
    for i, flag in enumerate(flags):
        if flag and start is None:
            start = i
        elif not flag and start is not None:
            yield start, i - start
            start = None
    if start is not None:
        yield start, len(flags) - start


def detect_dead_bands(img: Image.Image) -> list[Problem]:
    """Find flat, featureless strips — anywhere in the frame, not just at its edges.

    This is the check that would have caught the white band in the shipped v2
    render. That band sat *between* the banner and the photograph, so an
    edge-inward scan stopped at row 0 and never saw it. Scanning every run of
    uniform rows finds padding wherever the generator left it.
    """
    rgb = np.asarray(img.convert("RGB"), dtype=np.float32)
    g = rgb.mean(axis=2)
    h, w = g.shape
    problems: list[Problem] = []

    row_std = g.std(axis=1)
    row_span = (rgb.max(axis=1) - rgb.min(axis=1)).max(axis=1)
    flat = (row_std < DEAD_BAND_ROW_STD) & (row_span < DEAD_BAND_SPAN)

    # Padding is achromatic; a brand banner is not. Keying on brightness instead
    # ("is it near-white?") missed the real case: the shipped v2 band sat at 234,
    # a hair under a 235 cutoff, because JPEG never gives back exact white.
    # Uniform + colourless is the signal. A uniform *coloured* band is a graphic
    # the compositor drew, which measure_graphic_coverage judges instead.
    row_color = rgb.mean(axis=1)
    chroma = row_color.max(axis=1) - row_color.min(axis=1)
    achromatic = chroma < DEAD_BAND_MAX_CHROMA

    for start, length in _runs(flat & achromatic):
        frac = length / h
        if frac < DEAD_BAND_MIN_FRACTION:
            continue
        brightness = g[start:start + length].mean()
        tone = "white" if brightness > 200 else ("black" if brightness < 55 else "flat grey")
        if start <= 2:
            where = "the top edge"
        elif start + length >= h - 2:
            where = "the bottom edge"
        else:
            where = f"the middle of the frame (from y {start / h:.2f} to {(start + length) / h:.2f})"
        problems.append(
            Problem(
                category="photography",
                severity="high" if frac > 0.04 else "medium",
                issue=f"a flat {tone} band covers {frac:.0%} of the frame at {where} — "
                "the generated photograph is padded or letterboxed, not full-bleed",
                correction="regenerate the background with an explicit full-bleed instruction, "
                "or crop the padding off before compositing",
                element="background",
            )
        )
    return problems


def measure_graphic_coverage(img: Image.Image) -> list[Problem]:
    """How much of the frame is flat graphics rather than photograph.

    Perfectly uniform pixels essentially do not occur in a photograph, but they
    are exactly what a filled banner, a backing disc or a colour bar is made of.
    When that fraction gets large the creative has stopped being a photograph
    with brand furniture on it and become a template with a photo slot — which
    is what the full-width banner renders looked like.
    """
    g = np.asarray(img.convert("L"), dtype=np.float32)
    if g.shape[0] < 4 or g.shape[1] < 4:
        return []
    gy, gx = np.gradient(g)
    flat = (np.abs(gx) < 0.5) & (np.abs(gy) < 0.5)
    coverage = float(flat.mean())

    if coverage < GRAPHIC_COVERAGE_WARN:
        return []
    return [
        Problem(
            category="composition",
            severity="high" if coverage > GRAPHIC_COVERAGE_HIGH else "medium",
            issue=f"flat graphic fills cover {coverage:.0%} of the frame — the photograph is "
            "being crowded out by banners and panels rather than running full-bleed",
            correction="run the photography edge-to-edge and carry the copy in compact overlays "
            "instead of full-width colour bands",
            element="",
        )
    ]


def measure_element_contrast(
    composite: Image.Image, background: Image.Image | None, boxes: dict[str, Box]
) -> list[Problem]:
    """Compare each element's region in the composite against the same region in
    the background it was drawn onto. A composited element that barely changed
    its region did not survive the composite — the classic case being a
    light logo chroma-keyed onto a light backing disc.
    """
    if background is None:
        return []
    problems: list[Problem] = []
    if background.size != composite.size:
        background = background.resize(composite.size, Image.LANCZOS)
    comp, back = _gray(composite), _gray(background)
    h, w = comp.shape

    for name, box in boxes.items():
        if name in ("subject", "pointer"):
            continue
        x0, y0 = int(box.x * w), int(box.y * h)
        x1, y1 = int(box.x1 * w), int(box.y1 * h)
        x0, y0 = max(0, x0), max(0, y0)
        x1, y1 = min(w, x1), min(h, y1)
        if x1 - x0 < 4 or y1 - y0 < 4:
            continue
        diff = np.abs(comp[y0:y1, x0:x1] - back[y0:y1, x0:x1])
        rms = float(np.sqrt((diff**2).mean()))
        if rms < MIN_ELEMENT_CONTRAST:
            problems.append(
                Problem(
                    category="rendering",
                    severity="high",
                    issue=f"{name} is barely distinguishable from the background it was drawn on "
                    f"(RMS difference {rms:.1f}) — it is effectively invisible",
                    correction=f"give {name} a contrasting colour or backing for this photograph "
                    f"(e.g. swap the light logo asset for the dark one, or drop the backing disc)",
                    element=name,
                )
            )
    return problems


def thumbnail_test(
    composite: Image.Image, boxes: dict[str, Box], thumb_path: str | Path | None = None
) -> tuple[list[Problem], Path | None]:
    """Downscale to feed size and check the load-bearing elements still read.

    A creative that dissolves into even mush at 150px wide has no hierarchy,
    whatever it looks like at full size.
    """
    problems: list[Problem] = []
    ratio = THUMBNAIL_WIDTH / composite.width
    thumb = composite.resize(
        (THUMBNAIL_WIDTH, max(1, int(composite.height * ratio))), Image.LANCZOS
    )
    g = _gray(thumb)
    th, tw = g.shape

    saved: Path | None = None
    if thumb_path:
        saved = Path(thumb_path)
        saved.parent.mkdir(parents=True, exist_ok=True)
        thumb.save(saved)

    load_bearing = [n for n in ("subject", "headline", "cta") if n in boxes]
    details: dict[str, float] = {}
    for name in load_bearing:
        box = boxes[name]
        x0, y0 = max(0, int(box.x * tw)), max(0, int(box.y * th))
        x1, y1 = min(tw, int(box.x1 * tw)), min(th, int(box.y1 * th))
        if x1 - x0 < 3 or y1 - y0 < 3:
            problems.append(
                Problem(
                    category="legibility",
                    severity="high",
                    issue=f"{name} is smaller than 3px at thumbnail size — it disappears in feed",
                    correction=f"increase {name} scale substantially",
                    element=name,
                )
            )
            continue
        patch = g[y0:y1, x0:x1]
        gy, gx = np.gradient(patch)
        detail = float(np.sqrt(gx**2 + gy**2).mean())
        details[name] = detail
        if detail < MIN_THUMBNAIL_DETAIL:
            problems.append(
                Problem(
                    category="legibility",
                    severity="medium",
                    issue=f"{name} carries almost no visible structure at thumbnail size "
                    f"(detail {detail:.1f})",
                    correction=f"increase {name}'s size or contrast so it survives the feed crop",
                    element=name,
                )
            )

    # Everything equally busy is the "no hierarchy" signature.
    if len(details) >= 2:
        values = list(details.values())
        spread = (max(values) - min(values)) / (max(values) or 1)
        if spread < 0.12:
            problems.append(
                Problem(
                    category="hierarchy",
                    severity="medium",
                    issue="at thumbnail size every element carries roughly equal visual weight — "
                    "nothing leads the eye",
                    correction="enlarge the focal subject or reduce the supporting elements so one "
                    "element clearly dominates",
                    element="",
                )
            )

    return problems, saved


def estimate_subject_prominence(composite: Image.Image, boxes: dict[str, Box]) -> list[Problem]:
    """Does the declared subject region actually hold the image's detail?

    Uses gradient energy as a cheap saliency proxy: if the subject box holds far
    less of the frame's structure than its share of the area, the subject is
    buried in the background rather than being the focal point.
    """
    if "subject" not in boxes:
        return []
    g = _gray(composite)
    gy, gx = np.gradient(g)
    energy = np.sqrt(gx**2 + gy**2)
    total = float(energy.sum()) or 1.0
    h, w = g.shape
    box = boxes["subject"]
    x0, y0 = max(0, int(box.x * w)), max(0, int(box.y * h))
    x1, y1 = min(w, int(box.x1 * w)), min(h, int(box.y1 * h))
    if x1 <= x0 or y1 <= y0:
        return []
    share = float(energy[y0:y1, x0:x1].sum()) / total
    area_share = box.area

    if share < area_share * 0.75:
        return [
            Problem(
                category="product_prominence",
                severity="high" if share < area_share * 0.5 else "medium",
                issue=f"the subject region holds only {share:.0%} of the frame's visual detail "
                f"while occupying {area_share:.0%} of it — the product is not the focal point",
                correction="tighten the crop onto the product, increase subject scale by 15-20%, "
                "or simplify the surrounding environment",
                element="subject",
            )
        ]
    return []


def inspect(
    composite_path: str | Path,
    *,
    manifest: dict | None = None,
    background_path: str | Path | None = None,
    spec: dict | None = None,
    thumbnail_path: str | Path | None = None,
) -> dict:
    """Run every automated measurement against a rendered composite."""
    composite = Image.open(composite_path).convert("RGB")
    boxes: dict[str, Box] = {}
    if manifest:
        for name, values in (manifest.get("boxes") or {}).items():
            boxes[name] = Box(*values)

    problems: list[Problem] = []
    problems += detect_dead_bands(composite)
    problems += measure_graphic_coverage(composite)
    problems += estimate_subject_prominence(composite, boxes)

    background = None
    if background_path and Path(background_path).exists():
        background = Image.open(background_path).convert("RGB")
    problems += measure_element_contrast(composite, background, boxes)

    thumb_problems, thumb = thumbnail_test(composite, boxes, thumbnail_path)
    problems += thumb_problems

    # Geometry issues re-checked against what was ACTUALLY drawn, not the plan.
    if spec and boxes:
        for issue in validate_layout(spec, boxes):
            problems.append(
                Problem(
                    category=issue.category,
                    severity="high" if issue.severity == "error" else "medium",
                    issue=issue.message,
                    correction=issue.correction,
                    element=issue.element,
                )
            )

    return {
        "image": str(composite_path),
        "size": list(composite.size),
        "partial": not boxes,
        "thumbnail": str(thumb) if thumb else None,
        "problems": [p.to_dict() for p in problems],
        "measured_elements": sorted(boxes),
    }


# --------------------------------------------------------------------------
# Scoring and routing
# --------------------------------------------------------------------------


def _as_problems(items: list[dict] | None) -> list[Problem]:
    out: list[Problem] = []
    for raw in items or []:
        out.append(
            Problem(
                category=raw.get("category", "composition"),
                severity=raw.get("severity", "medium"),
                issue=raw.get("issue", ""),
                correction=raw.get("correction", ""),
                source=raw.get("source", "reviewer"),
                element=raw.get("element", ""),
                stage=raw.get("stage", ""),
            )
        )
    return out


def score(
    problems: list[Problem] | list[dict],
    *,
    revision: int = 0,
    max_revisions: int = MAX_REVISIONS,
) -> dict:
    """Turn problems into a rubric score, a decision, and a next action.

    Each problem deducts from the rubric category it belongs to, weighted by
    severity, and a category cannot go below zero — so one catastrophic area
    cannot drag the whole score negative and mask everything else.
    """
    if problems and isinstance(problems[0], dict):
        problems = _as_problems(problems)  # type: ignore[arg-type]
    problems = list(problems)  # type: ignore[assignment]

    deductions = {k: 0.0 for k in RUBRIC}
    for p in problems:  # type: ignore[union-attr]
        rubric_key = CATEGORY_TO_RUBRIC.get(p.category, "composition")
        weight = SEVERITY_WEIGHT.get(p.severity, 0.55)
        deductions[rubric_key] += RUBRIC[rubric_key] * weight

    breakdown = {}
    for key, maximum in RUBRIC.items():
        breakdown[key] = round(max(0.0, maximum - deductions[key]), 1)
    total = round(sum(breakdown.values()), 1)

    if total >= PASS_EXCELLENT:
        decision, band = "PASS", "excellent — publish-ready"
    elif total >= PASS_THRESHOLD:
        decision, band = "PASS", "good — minor improvements optional"
    elif total >= REVISE_THRESHOLD:
        decision, band = "REVISE", "needs revision"
    else:
        decision, band = "REJECT", "reject and regenerate"

    # A defect a viewer would notice blocks the ship regardless of the total.
    high_count = sum(1 for p in problems if p.severity == "high")  # type: ignore[union-attr]
    if high_count >= HIGH_SEVERITY_REJECT_COUNT:
        decision, band = "REJECT", f"{high_count} high-severity defects — reject and regenerate"
    elif high_count and decision == "PASS":
        decision = "REVISE"
        band = f"scored {total} but carries {high_count} high-severity defect(s) — revise"

    # Route to the cheapest stage that can actually fix the worst problems.
    routes = {p.route for p in problems if p.severity in ("high", "medium")}  # type: ignore[union-attr]
    next_action = "none"
    if decision != "PASS":
        for candidate in ROUTE_ORDER:
            if candidate in routes:
                next_action = candidate
                break
        else:
            next_action = "revise_spec"

    exhausted = revision >= max_revisions
    if decision != "PASS" and exhausted:
        next_action = "stop_below_threshold"

    return {
        "score": total,
        "breakdown": breakdown,
        "decision": decision,
        "band": band,
        "revision": revision,
        "max_revisions": max_revisions,
        "revisions_remaining": max(0, max_revisions - revision),
        "next_action": next_action,
        "problems": [p.to_dict() for p in problems],  # type: ignore[union-attr]
        "corrections": corrections_for(problems, next_action),  # type: ignore[arg-type]
        "passed": decision == "PASS",
        "below_threshold_final": decision != "PASS" and exhausted,
    }


def corrections_for(problems: list[Problem], route: str) -> list[str]:
    """The correction lines that the given stage should actually apply. The
    revision step feeds these straight back in — a critic whose output nothing
    consumes is just commentary."""
    if route in ("none", "stop_below_threshold"):
        route_filter = None
    else:
        route_filter = route
    out = []
    for p in sorted(problems, key=lambda x: -SEVERITY_WEIGHT.get(x.severity, 0.5)):
        if route_filter and p.route != route_filter:
            continue
        if p.correction and p.correction not in out:
            out.append(p.correction)
    return out


def review(
    composite_path: str | Path,
    *,
    manifest: dict | None = None,
    background_path: str | Path | None = None,
    spec: dict | None = None,
    reviewer_findings: list[dict] | None = None,
    revision: int = 0,
    max_revisions: int = MAX_REVISIONS,
    thumbnail_path: str | Path | None = None,
) -> dict:
    """Full gate: measure, merge the reviewer's findings, score, route."""
    measured = inspect(
        composite_path,
        manifest=manifest,
        background_path=background_path,
        spec=spec,
        thumbnail_path=thumbnail_path,
    )
    problems = _as_problems(measured["problems"]) + _as_problems(reviewer_findings)
    for p, raw in zip(problems, measured["problems"] + list(reviewer_findings or [])):
        p.source = raw.get("source", p.source)
    result = score(problems, revision=revision, max_revisions=max_revisions)
    result["image"] = measured["image"]
    result["partial"] = measured["partial"]
    result["thumbnail"] = measured["thumbnail"]
    result["measured_elements"] = measured["measured_elements"]
    return result


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("composite", help="Final composited PNG to inspect")
    p.add_argument("--manifest", help="Render manifest emitted by compose_slide.py --manifest")
    p.add_argument("--background", help="The background photo the composite was built on")
    p.add_argument("--spec", help="The design spec used, for geometry re-validation")
    p.add_argument("--findings", help="JSON file of reviewer findings to merge in")
    p.add_argument("--revision", type=int, default=0, help="Which revision cycle this is (0 = first pass)")
    p.add_argument("--max-revisions", type=int, default=MAX_REVISIONS)
    p.add_argument("--thumbnail", help="Write the thumbnail-test image here")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8")) if args.manifest else None
    spec = json.loads(Path(args.spec).read_text(encoding="utf-8")) if args.spec else None
    findings = json.loads(Path(args.findings).read_text(encoding="utf-8")) if args.findings else None
    if isinstance(findings, dict):
        findings = findings.get("problems") or findings.get("findings")

    result = review(
        args.composite,
        manifest=manifest,
        background_path=args.background,
        spec=spec,
        reviewer_findings=findings,
        revision=args.revision,
        max_revisions=args.max_revisions,
        thumbnail_path=args.thumbnail,
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"score {result['score']}/100 — {result['decision']} ({result['band']})")
        for key, value in result["breakdown"].items():
            print(f"  {key:<20} {value:>5} / {RUBRIC[key]}")
        for prob in result["problems"]:
            print(f"  [{prob['severity']}] {prob['category']}/{prob['route']}: {prob['issue']}")
            if prob["correction"]:
                print(f"        -> {prob['correction']}")
        if result.get("partial"):
            print("  NOTE: no --manifest supplied — geometry, contrast and thumbnail checks "
                  "were skipped. This score covers photography checks only.")
        print(f"next action: {result['next_action']} "
              f"({result['revisions_remaining']} revision(s) remaining)")
        if result["below_threshold_final"]:
            print("REVISION BUDGET EXHAUSTED — this did not reach the threshold. "
                  "Keep the best candidate and say so; do not report it as passing.")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
