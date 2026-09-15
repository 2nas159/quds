#!/usr/bin/env python3
"""
Design Spec — the structured composition plan that sits between "approved copy"
and "generated image + composited PNG".

Why this module exists
----------------------
The failure mode it fixes: the image prompt and the compositor used to decide
layout *independently*. The prompt said "leave negative space in the upper
third"; the compose_slide.py command then dropped the label at y=0.40 because
someone typed 0.40. Nothing connected the two, so the label landed on the
product while the reserved empty space went unused.

Here, one Design Spec resolves into concrete normalized boxes. Those same boxes
produce (a) the "keep this region visually quiet" clauses in the image prompt
and (b) the placement arguments for the compositor. They cannot drift apart
because they are the same numbers.

Everything here is pure stdlib and brand-agnostic. All brand-specific values
(colors, fonts, logo paths, photography direction, measured layout calibration)
come from a brand profile JSON passed in at runtime — see `load_brand_profile`.

Coordinates are normalized fractions of the canvas (0..1), origin top-left.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path

SCHEMA_VERSION = "1.0"

# --------------------------------------------------------------------------
# Geometry
# --------------------------------------------------------------------------


@dataclass
class Box:
    """A normalized rectangle. `x`/`y` are the top-left corner."""

    x: float
    y: float
    w: float
    h: float

    @property
    def x1(self) -> float:
        return self.x + self.w

    @property
    def y1(self) -> float:
        return self.y + self.h

    @property
    def area(self) -> float:
        return max(0.0, self.w) * max(0.0, self.h)

    @property
    def center(self) -> tuple[float, float]:
        return (self.x + self.w / 2, self.y + self.h / 2)

    def intersection(self, other: "Box") -> "Box":
        x0 = max(self.x, other.x)
        y0 = max(self.y, other.y)
        x1 = min(self.x1, other.x1)
        y1 = min(self.y1, other.y1)
        return Box(x0, y0, max(0.0, x1 - x0), max(0.0, y1 - y0))

    def overlap_ratio(self, other: "Box") -> float:
        """Intersection area as a fraction of *this* box's area — i.e. how much
        of this element is covered. Asymmetric on purpose: a tiny badge sitting
        entirely on a huge product is 100% blocked, the product is barely
        touched, and those are different problems."""
        if self.area <= 0:
            return 0.0
        return self.intersection(other).area / self.area

    def inflate(self, pad: float) -> "Box":
        return Box(self.x - pad, self.y - pad, self.w + 2 * pad, self.h + 2 * pad)

    def clamp_into(self, bounds: "Box") -> "Box":
        """Slide (never resize) this box so it sits inside `bounds` where it
        can; if it is genuinely too big, pin it to the top-left of bounds."""
        w = min(self.w, bounds.w)
        h = min(self.h, bounds.h)
        x = min(max(self.x, bounds.x), bounds.x1 - w)
        y = min(max(self.y, bounds.y), bounds.y1 - h)
        return Box(x, y, w, h)

    def as_tuple(self) -> tuple[float, float, float, float]:
        return (self.x, self.y, self.w, self.h)

    def to_pixels(self, canvas_w: int, canvas_h: int) -> tuple[int, int, int, int]:
        return (
            int(round(self.x * canvas_w)),
            int(round(self.y * canvas_h)),
            int(round(self.w * canvas_w)),
            int(round(self.h * canvas_h)),
        )


# Named regions on a 3x3 grid, as (anchor_x, anchor_y) plus which corner of the
# element the anchor refers to. "Areas" are how a human art-directs ("put the
# hook upper-left"); boxes are what the renderer and the image prompt need.
AREAS: dict[str, tuple[float, float, str, str]] = {
    "upper_left": (0.0, 0.0, "left", "top"),
    "upper_center": (0.5, 0.0, "center", "top"),
    "upper_right": (1.0, 0.0, "right", "top"),
    "mid_left": (0.0, 0.5, "left", "middle"),
    "center": (0.5, 0.5, "center", "middle"),
    "mid_right": (1.0, 0.5, "right", "middle"),
    "lower_left": (0.0, 1.0, "left", "bottom"),
    "lower_center": (0.5, 1.0, "center", "bottom"),
    "lower_right": (1.0, 1.0, "right", "bottom"),
}

# Corner aliases used by the compositor's --logo-position vocabulary.
CORNER_ALIASES = {
    "tl": "upper_left",
    "tr": "upper_right",
    "bl": "lower_left",
    "br": "lower_right",
    "top_left": "upper_left",
    "top_right": "upper_right",
    "bottom_left": "lower_left",
    "bottom_right": "lower_right",
    "bottom_center": "lower_center",
    "top_center": "upper_center",
    "center_left": "mid_left",
    "center_right": "mid_right",
}


def normalize_area(name: str) -> str:
    key = (name or "").strip().lower()
    key = CORNER_ALIASES.get(key, key)
    if key not in AREAS:
        raise SpecError(
            f"unknown area {name!r}; expected one of {sorted(AREAS)} "
            f"or an alias {sorted(CORNER_ALIASES)}"
        )
    return key


def area_to_corner(name: str) -> str:
    """Map an area back to the compositor's tl/tr/bl/br vocabulary."""
    area = normalize_area(name)
    vert = "t" if area.startswith("upper") else ("b" if area.startswith("lower") else "t")
    horiz = "l" if area.endswith("left") else ("r" if area.endswith("right") else "l")
    return vert + horiz


def place(area: str, w: float, h: float, margin: float, margin_y: float | None = None) -> Box:
    """Resolve a named area plus an element size into a concrete Box, inset by
    the outer margin. Center areas center the element on the axis."""
    area = normalize_area(area)
    ax, ay, halign, valign = AREAS[area]
    my = margin if margin_y is None else margin_y

    if halign == "left":
        x = margin
    elif halign == "right":
        x = 1.0 - margin - w
    else:
        x = ax - w / 2

    if valign == "top":
        y = my
    elif valign == "bottom":
        y = 1.0 - my - h
    else:
        y = ay - h / 2

    return Box(x, y, w, h)


class SpecError(ValueError):
    """A Design Spec that cannot be resolved into a layout at all."""


# --------------------------------------------------------------------------
# Creative types — generic composition patterns, not brand content
# --------------------------------------------------------------------------
# Each preset declares the element set, the visual hierarchy, and nominal
# geometry. Brand-measured numbers override these via the brand profile's
# `layout_calibration` block, and an individual spec overrides both.

# The bottom band carries three things in a fixed reading order: badge, then
# the action, then the contact line flush to the safe edge. These y values
# mirror what compose_slide.py actually renders (the CTA is stacked above the
# footer block, the badge above that), so the plan and the render agree instead
# of all three defaulting flush-bottom and colliding.
FOOTER_STACK_Y = None  # flush to the bottom safe edge, computed from the margin
CTA_STACK_Y = 0.836
BADGE_STACK_Y = 0.720
# Copy lists sit in the upper band, under the hook — never across the subject.
BULLETS_STACK_Y = 0.200

CREATIVE_TYPES: dict[str, dict] = {
    "hero_offer": {
        "description": "One product, one message. The default feed/ad frame.",
        "hierarchy": ["subject", "headline", "cta", "badge", "logo", "footer"],
        "max_coverage": 0.72,
        "subject_area_locked": False,
        "subject": {"area": "center", "coverage": 0.58, "crop": "tight", "camera": "slight_overhead"},
        "elements": {
            "headline": {"area": "upper_left", "max_width": 0.50, "rotation": -3.0},
            "logo": {"area": "upper_right", "width": 0.13},
            "cta": {"area": "lower_center", "width": 0.43, "y": CTA_STACK_Y},
            "badge": {"area": "lower_left", "width": 0.21, "y": BADGE_STACK_Y},
            "footer": {"area": "lower_left", "width": 0.60},
        },
    },
    "documentary_trust": {
        "description": "Hands/process in a real working environment. Trust-building, "
        "more context than product close-up.",
        "hierarchy": ["subject", "headline", "bullets", "cta", "logo", "footer"],
        "max_coverage": 0.60,
        # The copy band above the subject only stays clear if the subject stays
        # put, so a candidate may not relocate it here.
        "subject_area_locked": True,
        # Subject sits low so the copy band above it is genuinely empty photograph
        # rather than text dropped onto the product.
        "subject": {"area": "lower_center", "coverage": 0.45, "crop": "medium", "camera": "slight_overhead"},
        "elements": {
            "headline": {"area": "upper_left", "max_width": 0.46, "rotation": -3.0},
            "bullets": {"area": "upper_right", "max_width": 0.62, "y": BULLETS_STACK_Y},
            "logo": {"area": "upper_right", "width": 0.12},
            "cta": {"area": "lower_center", "width": 0.40, "y": CTA_STACK_Y},
            "footer": {"area": "lower_left", "width": 0.60},
        },
    },
    "value_list": {
        "description": "Educational / mid-carousel slide. Copy carries the frame, "
        "photography supports it.",
        "hierarchy": ["headline", "bullets", "subject", "logo", "footer"],
        "max_coverage": 0.50,
        "subject_area_locked": True,
        "subject": {"area": "lower_center", "coverage": 0.35, "crop": "wide", "camera": "directly_overhead"},
        "elements": {
            "headline": {"area": "upper_left", "max_width": 0.52, "rotation": -3.0},
            "bullets": {"area": "upper_right", "max_width": 0.70, "y": BULLETS_STACK_Y},
            "logo": {"area": "upper_right", "width": 0.12},
            "footer": {"area": "lower_left", "width": 0.60},
        },
    },
    "cta_close": {
        "description": "Final carousel slide. The action is the point; product is "
        "present but no longer the hero.",
        "hierarchy": ["headline", "cta", "subject", "footer", "logo"],
        "max_coverage": 0.55,
        "subject_area_locked": False,
        "subject": {"area": "center", "coverage": 0.40, "crop": "medium", "camera": "slight_overhead"},
        "elements": {
            "headline": {"area": "upper_left", "max_width": 0.52, "rotation": -3.0},
            "logo": {"area": "upper_right", "width": 0.12},
            "cta": {"area": "lower_center", "width": 0.50, "y": CTA_STACK_Y},
            "footer": {"area": "lower_left", "width": 0.65},
        },
    },
}

DEFAULT_CREATIVE_TYPE = "hero_offer"

# --------------------------------------------------------------------------
# Candidate art directions
# --------------------------------------------------------------------------
# Three genuinely different compositions, not three rewordings of one prompt.
# Each shifts subject scale, crop, camera and where the negative space sits, so
# the resulting photographs differ in kind rather than in adjectives.

# A candidate SCALES the creative type's subject budget rather than replacing
# it, and may only relocate the subject when the creative type allows it. The
# two axes are not independent: a very large centred subject and a layout with
# a copy band are contradictory, and letting a candidate override the area
# outright produced layouts the validator itself rejected.
CANDIDATES: dict[str, dict] = {
    "product_hero": {
        "label": "A — PRODUCT HERO",
        "intent": "Maximum product impact. Very large subject, tight crop, minimal environment.",
        "subject": {"coverage_multiplier": 1.17, "crop": "tight",
                    "camera": "directly_overhead", "area": "center"},
        "headline_area": "upper_left",
        "environment_weight": "minimal",
    },
    "documentary": {
        "label": "B — DOCUMENTARY",
        "intent": "Trust through process. Gloved hands working, more of the real environment visible.",
        "subject": {"coverage_multiplier": 0.83, "crop": "medium",
                    "camera": "slight_overhead", "area": "lower_center"},
        "headline_area": "upper_left",
        "environment_weight": "present",
    },
    "commercial": {
        "label": "C — COMMERCIAL",
        "intent": "Aggressive hierarchy. Tight three-quarter framing with the subject driven into the "
        "lower-right, opening a decisive diagonal block of negative space across the upper-left.",
        # The subject sits low-right rather than centred: that is what actually
        # frees a corner for the hook. A vertically centred hook beside a
        # dominant product is geometrically impossible — the product is simply
        # wider than the space left over — so this direction opens the corner
        # instead of pretending the middle band is free.
        "subject": {"coverage_multiplier": 1.0, "crop": "tight",
                    "camera": "three_quarter", "area": "lower_right"},
        "headline_area": "upper_left",
        "environment_weight": "minimal",
    },
}

DEFAULT_CANDIDATES = ["product_hero", "documentary", "commercial"]

# Nominal on-canvas heights used for *planning* only. The compositor measures
# the real thing after text shaping and re-validates with actual boxes — these
# just have to be close enough to catch a bad plan before an image is paid for.
NOMINAL_HEIGHTS = {
    "headline": 0.105,
    "subtext": 0.035,
    "bullets": 0.20,
    "cta": 0.062,
    "badge": 0.176,
    "footer": 0.030,
    "logo": 0.105,
}

ASPECT_PRESETS = {
    "4:5": (1080, 1350),
    "1:1": (1080, 1080),
    "3:4": (1080, 1440),
    "9:16": (1080, 1920),
    "1.91:1": (1200, 628),
}

DEFAULT_MARGIN = 0.045


# --------------------------------------------------------------------------
# Brand profile
# --------------------------------------------------------------------------


def load_brand_profile(path: str | Path) -> dict:
    """Brand-specific values live entirely in this file, never in this module.
    Swapping it (plus the font/logo assets it points at) is what makes the skill
    reusable for another brand."""
    p = Path(path)
    if not p.exists():
        raise SpecError(
            f"brand profile not found at {p}. It holds every brand-specific value "
            "(palette, fonts, logo assets, photography direction, measured layout "
            "calibration) that this skill deliberately does not hardcode."
        )
    with p.open(encoding="utf-8") as fh:
        profile = json.load(fh)
    for required in ("colors", "photography", "layout_calibration"):
        if required not in profile:
            raise SpecError(f"brand profile {p} is missing required section {required!r}")
    return profile


# --------------------------------------------------------------------------
# Spec construction
# --------------------------------------------------------------------------


def _deep_merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def build_spec(
    *,
    creative_type: str = DEFAULT_CREATIVE_TYPE,
    candidate: str | None = None,
    aspect: str = "4:5",
    canvas: dict | None = None,
    brand_profile: dict | None = None,
    overrides: dict | None = None,
) -> dict:
    """Compose a Design Spec from: creative-type preset -> candidate art
    direction -> brand calibration -> explicit overrides. Later wins."""
    if creative_type not in CREATIVE_TYPES:
        raise SpecError(
            f"unknown creative_type {creative_type!r}; expected one of {sorted(CREATIVE_TYPES)}"
        )
    preset = CREATIVE_TYPES[creative_type]

    if canvas:
        cw, ch = int(canvas["width"]), int(canvas["height"])
    else:
        if aspect not in ASPECT_PRESETS:
            raise SpecError(f"unknown aspect {aspect!r}; expected one of {sorted(ASPECT_PRESETS)}")
        cw, ch = ASPECT_PRESETS[aspect]

    spec: dict = {
        "schema_version": SCHEMA_VERSION,
        "canvas": {"width": cw, "height": ch, "aspect": aspect},
        "creative_type": creative_type,
        "candidate": candidate,
        "visual_objective": "",
        "margin": DEFAULT_MARGIN,
        "hierarchy": list(preset["hierarchy"]),
        "subject": dict(preset["subject"]),
        "composition": {
            "camera": preset["subject"].get("camera", "slight_overhead"),
            "crop": preset["subject"].get("crop", "tight"),
            "focal_point": "subject",
            "environment_weight": "present",
        },
        "elements": {k: dict(v) for k, v in preset["elements"].items()},
        "avoid": [],
    }

    if candidate:
        if candidate not in CANDIDATES:
            raise SpecError(f"unknown candidate {candidate!r}; expected one of {sorted(CANDIDATES)}")
        cand = CANDIDATES[candidate]
        cs = cand["subject"]
        base_coverage = float(spec["subject"].get("coverage", 0.55))
        max_coverage = float(preset.get("max_coverage", MAX_SUBJECT_COVERAGE))
        spec["subject"]["coverage"] = round(
            min(base_coverage * cs.get("coverage_multiplier", 1.0), max_coverage), 4)
        spec["subject"]["crop"] = cs["crop"]
        spec["subject"]["camera"] = cs["camera"]
        if not preset.get("subject_area_locked"):
            spec["subject"]["area"] = cs["area"]
        spec["composition"]["camera"] = cs["camera"]
        spec["composition"]["crop"] = cs["crop"]
        spec["composition"]["environment_weight"] = cand["environment_weight"]
        if "headline" in spec["elements"]:
            spec["elements"]["headline"]["area"] = cand["headline_area"]

    if brand_profile:
        cal = brand_profile.get("layout_calibration", {})
        spec["margin"] = cal.get("margin", spec["margin"])
        for name, values in (cal.get("elements") or {}).items():
            if name in spec["elements"]:
                spec["elements"][name] = _deep_merge(spec["elements"][name], values)
        spec["avoid"] = list(brand_profile.get("photography", {}).get("avoid", []))
        spec["colors"] = dict(brand_profile.get("colors", {}))

    if overrides:
        spec = _deep_merge(spec, overrides)

    return spec


def resolve_subject_box(spec: dict) -> Box:
    """The subject's footprint. Explicit x/y/w/h wins; otherwise derive a box of
    the requested coverage, centred on the requested area."""
    subj = spec.get("subject", {})
    if all(k in subj for k in ("x", "y", "w", "h")):
        return Box(float(subj["x"]), float(subj["y"]), float(subj["w"]), float(subj["h"]))

    coverage = float(subj.get("coverage", 0.55))
    coverage = min(max(coverage, 0.05), 0.95)
    # Treat coverage as the fraction of canvas AREA the subject occupies, and
    # derive a roughly square footprint from it. A tight crop reads wider than
    # tall on a portrait canvas, hence the mild aspect bias.
    side = coverage**0.5
    w = min(0.95, side * 1.12)
    h = min(0.95, side * 0.98)

    area = normalize_area(subj.get("area", "center"))
    ax, ay, _, _ = AREAS[area]
    # Subjects sit *toward* an area rather than flush against the edge — a
    # product pinned to the frame edge reads as a crop accident.
    cx = 0.5 + (ax - 0.5) * 0.42
    cy = 0.5 + (ay - 0.5) * 0.42
    # A subject can extend past the frame (that is what a tight crop means), but
    # its box must describe the visible footprint or every overlap check is
    # computed against pixels that do not exist.
    return Box(cx - w / 2, cy - h / 2, w, h).clamp_into(Box(0.0, 0.0, 1.0, 1.0))


# A product photographed edge-to-edge technically "occupies" most of the frame,
# so testing text against the whole subject box would flag every layout. What
# actually matters is the focal core — the centre of the cut, where an overlay
# genuinely destroys the shot. Text grazing the outer edge of the product is
# ordinary design.
SUBJECT_CORE_SCALE = 0.72


def subject_core(box: Box) -> Box:
    w, h = box.w * SUBJECT_CORE_SCALE, box.h * SUBJECT_CORE_SCALE
    cx, cy = box.center
    return Box(cx - w / 2, cy - h / 2, w, h)


def safe_frame(spec: dict) -> Box:
    """The usable area inside the outer margin.

    The margin is a fraction of canvas WIDTH and is applied as an equal pixel
    inset on all four edges — which is what compose_slide.py actually draws.
    Treating it as a fraction of height as well put the safe frame in a
    different place from the renderer on any non-square canvas, so a correctly
    placed footer was reported as breaking the margin.
    """
    margin = float(spec.get("margin", DEFAULT_MARGIN))
    canvas = spec.get("canvas") or {}
    w, h = canvas.get("width", 1080), canvas.get("height", 1350)
    margin_y = margin * (w / h) if h else margin
    return Box(margin, margin_y, 1 - 2 * margin, 1 - 2 * margin_y)


def resolve_layout(spec: dict, measured: dict[str, Box] | None = None) -> dict[str, Box]:
    """Resolve every declared element into a concrete Box.

    `measured` lets the compositor substitute the real post-shaping geometry of
    an element for the planning estimate, so the same collision rules run
    against what will actually be drawn.
    """
    frame = safe_frame(spec)
    margin, margin_y = frame.x, frame.y
    elements = spec.get("elements", {})
    boxes: dict[str, Box] = {"subject": resolve_subject_box(spec)}

    for name, cfg in elements.items():
        if cfg is None or cfg.get("enabled") is False:
            continue
        if measured and name in measured:
            boxes[name] = measured[name]
            continue
        if all(k in cfg for k in ("x", "y", "w", "h")):
            boxes[name] = Box(float(cfg["x"]), float(cfg["y"]), float(cfg["w"]), float(cfg["h"]))
            continue

        w = float(cfg.get("width", cfg.get("max_width", 0.40)))
        h = float(cfg.get("height", NOMINAL_HEIGHTS.get(name, 0.08)))
        box = place(cfg.get("area", "upper_left"), w, h, margin, margin_y)
        # Explicit x/y still steer a planned box (the compositor's --label-x/-y
        # equivalents) without requiring the caller to supply a size too.
        if "x" in cfg:
            box = Box(float(cfg["x"]), box.y, box.w, box.h)
        if "y" in cfg:
            box = Box(box.x, float(cfg["y"]), box.w, box.h)
        boxes[name] = box

    return boxes


# --------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------

# Elements that legitimately sit over photography (but not over the subject's
# focal core) versus ones whose overlap is always a mistake.
PHOTO_SAFE = {"footer", "cta", "logo", "watermark", "pointer"}

# Proportion limits that keep hierarchy intact. These are the guards against
# "oversized logo / oversized CTA / headline spanning the whole canvas".
PROPORTION_LIMITS = {
    "logo": {"max_width": 0.22, "note": "an oversized logo competes with the product"},
    "cta": {"max_width": 0.62, "note": "the CTA supports the offer, it is not the offer"},
    "badge": {"max_width": 0.30, "note": "a badge is an accent, not a second subject"},
    "headline": {"max_width": 0.72, "note": "a headline spanning the canvas reads as a template"},
    "footer": {"max_width": 0.80, "note": "the contact line is supporting information"},
}

MIN_SUBJECT_COVERAGE = 0.22
MAX_SUBJECT_COVERAGE = 0.85
# Fraction of a lower-priority element that may sit on a higher-priority one
# before it counts as a collision rather than a graze.
OVERLAP_TOLERANCE = 0.12
# How much of the subject the text furniture may cover in total.
MAX_SUBJECT_OCCLUSION = 0.22
# How much of a text element may sit on the subject's focal core before it
# counts as covering the product rather than sitting beside it.
SUBJECT_OVERLAP_TOLERANCE = 0.35


@dataclass
class Issue:
    severity: str  # "error" | "warning"
    category: str  # "collision" | "proportion" | "safe_area" | "hierarchy" | "schema"
    element: str
    message: str
    correction: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _priority_index(spec: dict, name: str) -> int:
    hierarchy = spec.get("hierarchy", [])
    return hierarchy.index(name) if name in hierarchy else len(hierarchy) + 1


def validate_layout(spec: dict, boxes: dict[str, Box] | None = None) -> list[Issue]:
    """Structural checks on a resolved layout. Returns issues rather than
    raising, so a caller can auto-correct what it can and report the rest."""
    issues: list[Issue] = []
    boxes = boxes if boxes is not None else resolve_layout(spec)
    frame = safe_frame(spec)
    margin = frame.x

    # --- subject prominence -------------------------------------------------
    subject = boxes.get("subject")
    if subject is not None:
        if subject.area < MIN_SUBJECT_COVERAGE:
            issues.append(
                Issue(
                    "error",
                    "hierarchy",
                    "subject",
                    f"subject occupies {subject.area:.0%} of the frame — an empty composition "
                    f"with a small subject reads as a stock photo with a caption",
                    f"raise subject.coverage to at least {MIN_SUBJECT_COVERAGE:.0%}",
                )
            )
        elif subject.area > MAX_SUBJECT_COVERAGE:
            issues.append(
                Issue(
                    "warning",
                    "hierarchy",
                    "subject",
                    f"subject occupies {subject.area:.0%} of the frame, leaving no room for "
                    "the text furniture to breathe",
                    f"lower subject.coverage below {MAX_SUBJECT_COVERAGE:.0%}",
                )
            )

    # --- safe areas ---------------------------------------------------------
    # Elements are placed at integer pixels, so a box can land a fraction of a
    # normalized unit outside the frame purely from rounding. Tolerate about a
    # pixel and a half rather than reporting a rounding artefact as a design error.
    canvas = spec.get("canvas") or {}
    eps_x = 1.5 / canvas.get("width", 1080)
    eps_y = 1.5 / canvas.get("height", 1350)

    for name, box in boxes.items():
        if name == "subject":
            continue  # photography is deliberately full-bleed
        if (box.x < frame.x - eps_x or box.y < frame.y - eps_y
                or box.x1 > frame.x1 + eps_x or box.y1 > frame.y1 + eps_y):
            issues.append(
                Issue(
                    "error",
                    "safe_area",
                    name,
                    f"{name} breaks the {margin:.1%} outer margin "
                    f"(box {box.x:.3f},{box.y:.3f} {box.w:.3f}x{box.h:.3f})",
                    f"move {name} inside the safe frame or reduce its width",
                )
            )

    # --- proportions --------------------------------------------------------
    for name, limit in PROPORTION_LIMITS.items():
        box = boxes.get(name)
        if box is None:
            continue
        if box.w > limit["max_width"] + 1e-6:
            issues.append(
                Issue(
                    "error",
                    "proportion",
                    name,
                    f"{name} is {box.w:.0%} of canvas width, over the {limit['max_width']:.0%} "
                    f"limit — {limit['note']}",
                    f"reduce {name} width to at most {limit['max_width']:.0%}",
                )
            )

    # --- element-to-element collisions -------------------------------------
    names = [n for n in boxes if n != "subject"]
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            ba, bb = boxes[a], boxes[b]
            ratio_a = ba.overlap_ratio(bb)
            ratio_b = bb.overlap_ratio(ba)
            worst = max(ratio_a, ratio_b)
            if worst <= OVERLAP_TOLERANCE:
                continue
            loser = a if _priority_index(spec, a) > _priority_index(spec, b) else b
            winner = b if loser == a else a
            issues.append(
                Issue(
                    "error",
                    "collision",
                    loser,
                    f"{a} and {b} overlap ({worst:.0%} of the smaller element is covered)",
                    f"move {loser} clear of {winner} — {winner} outranks it in the hierarchy",
                )
            )

    # --- text furniture sitting on the subject ------------------------------
    if subject is not None:
        core = subject_core(subject)
        occluded = 0.0
        for name, box in boxes.items():
            if name == "subject" or name in PHOTO_SAFE:
                continue
            occluded += subject.overlap_ratio(box)
            # How much of THIS element sits on the product's focal core. A hook
            # label is supposed to sit beside the cut it names, not on it.
            on_core = box.overlap_ratio(core)
            if on_core > SUBJECT_OVERLAP_TOLERANCE:
                issues.append(
                    Issue(
                        "error",
                        "collision",
                        name,
                        f"{on_core:.0%} of {name} sits on the focal core of the subject — "
                        f"it covers the product instead of sitting beside it",
                        f"relocate {name} into reserved negative space, away from the subject",
                    )
                )
        if occluded > MAX_SUBJECT_OCCLUSION:
            issues.append(
                Issue(
                    "warning",
                    "hierarchy",
                    "subject",
                    f"text furniture covers {occluded:.0%} of the subject in total",
                    "reduce the number or size of overlaid elements",
                )
            )

    # --- hierarchy sanity ---------------------------------------------------
    hl, cta, logo = boxes.get("headline"), boxes.get("cta"), boxes.get("logo")
    if hl is not None and logo is not None and logo.area > hl.area:
        issues.append(
            Issue(
                "warning",
                "hierarchy",
                "logo",
                "the logo has a larger footprint than the headline",
                "shrink the logo — branding sits below the hook in the hierarchy",
            )
        )
    if hl is not None and cta is not None and cta.area > hl.area * 1.35:
        issues.append(
            Issue(
                "warning",
                "hierarchy",
                "cta",
                "the CTA has a much larger footprint than the headline",
                "shrink the CTA or strengthen the headline",
            )
        )

    return issues


def resolve_collisions(spec: dict, boxes: dict[str, Box], max_passes: int = 4) -> tuple[dict[str, Box], list[str]]:
    """Nudge lower-priority elements off higher-priority ones, in hierarchy
    order. Returns the adjusted boxes and a log of what moved.

    Deliberately conservative: it slides an element along the axis with the
    smaller required displacement and keeps it inside the safe frame. It never
    resizes and never reorders — if it cannot find room, validate_layout still
    reports the collision, which is the honest outcome."""
    frame = safe_frame(spec)
    out = {k: Box(*v.as_tuple()) for k, v in boxes.items()}
    log: list[str] = []

    movable = sorted(
        (n for n in out if n != "subject"),
        key=lambda n: _priority_index(spec, n),
    )

    # Pull anything already outside the safe frame back in before resolving
    # overlaps — otherwise an element that collides with nothing keeps its
    # out-of-frame position and only gets reported, never fixed.
    for name in movable:
        pulled = out[name].clamp_into(frame)
        # Only report a move a person would see. Integer pixel rounding shifts
        # a box by a fraction of a normalized unit on nearly every element, and
        # logging those buries the real adjustments in noise.
        if max(abs(pulled.x - out[name].x), abs(pulled.y - out[name].y)) > 0.001:
            log.append(
                f"pulled {name} back inside the safe frame: "
                f"({out[name].x:.3f},{out[name].y:.3f}) -> ({pulled.x:.3f},{pulled.y:.3f})"
            )
            out[name] = pulled

    for _ in range(max_passes):
        moved = False
        for idx, name in enumerate(movable):
            box = out[name]
            blockers = [movable[j] for j in range(idx)]
            if name not in PHOTO_SAFE and "subject" in out:
                blockers = blockers + ["subject"]
            for other in blockers:
                if other == "subject":
                    obox = subject_core(out["subject"])
                    if box.overlap_ratio(obox) <= SUBJECT_OVERLAP_TOLERANCE:
                        continue
                else:
                    obox = out[other]
                    if max(box.overlap_ratio(obox), obox.overlap_ratio(box)) <= OVERLAP_TOLERANCE:
                        continue
                inter = box.intersection(obox)
                if inter.area <= 0:
                    continue
                # Smaller of the two escape distances, signed away from the blocker.
                dy = inter.h if box.center[1] >= obox.center[1] else -inter.h
                dx = inter.w if box.center[0] >= obox.center[0] else -inter.w
                cand_y = Box(box.x, box.y + dy, box.w, box.h).clamp_into(frame)
                cand_x = Box(box.x + dx, box.y, box.w, box.h).clamp_into(frame)
                pick = cand_y if abs(dy) <= abs(dx) else cand_x
                if max(pick.overlap_ratio(obox), obox.overlap_ratio(pick)) >= max(
                    box.overlap_ratio(obox), obox.overlap_ratio(box)
                ):
                    alt = cand_x if pick is cand_y else cand_y
                    if max(alt.overlap_ratio(obox), obox.overlap_ratio(alt)) < max(
                        pick.overlap_ratio(obox), obox.overlap_ratio(pick)
                    ):
                        pick = alt
                if (round(pick.x, 5), round(pick.y, 5)) != (round(box.x, 5), round(box.y, 5)):
                    log.append(
                        f"moved {name} clear of {other}: "
                        f"({box.x:.3f},{box.y:.3f}) -> ({pick.x:.3f},{pick.y:.3f})"
                    )
                    out[name] = box = pick
                    moved = True
        if not moved:
            break

    return out, log


# --------------------------------------------------------------------------
# Negative space — the link between layout and image prompt
# --------------------------------------------------------------------------


def negative_space_regions(spec: dict, boxes: dict[str, Box] | None = None) -> list[dict]:
    """Where the photograph must stay visually quiet, derived from where the
    text furniture actually lands. This is what stops the image prompt and the
    compositor from disagreeing about the composition."""
    boxes = boxes if boxes is not None else resolve_layout(spec)
    regions: list[dict] = []
    for name, box in boxes.items():
        if name == "subject":
            continue
        padded = box.inflate(0.02)
        regions.append(
            {
                "for": name,
                "area": nearest_area(padded),
                "box": [round(v, 4) for v in padded.as_tuple()],
                "priority": _priority_index(spec, name),
            }
        )
    regions.sort(key=lambda r: r["priority"])
    return regions


def nearest_area(box: Box) -> str:
    """Name the 3x3 region a box mostly sits in — for prose in the image
    prompt, where "upper-left" communicates better than four decimals."""
    cx, cy = box.center
    col = "left" if cx < 1 / 3 else ("right" if cx > 2 / 3 else "center")
    row = "upper" if cy < 1 / 3 else ("lower" if cy > 2 / 3 else "mid")
    if row == "mid":
        return {"left": "mid_left", "center": "center", "right": "mid_right"}[col]
    return f"{row}_{col}" if col != "center" else f"{row}_center"


# --------------------------------------------------------------------------
# I/O
# --------------------------------------------------------------------------


def load_spec(path: str | Path) -> dict:
    p = Path(path)
    if not p.exists():
        raise SpecError(f"design spec not found: {p}")
    try:
        with p.open(encoding="utf-8") as fh:
            spec = json.load(fh)
    except json.JSONDecodeError as exc:
        raise SpecError(f"design spec {p} is not valid JSON: {exc}") from exc
    return validate_schema(spec)


def validate_schema(spec: dict) -> dict:
    """Structural validation of the document itself, before any geometry is
    resolved. Raises SpecError with an actionable message."""
    if not isinstance(spec, dict):
        raise SpecError("design spec must be a JSON object")

    canvas = spec.get("canvas")
    if not isinstance(canvas, dict) or "width" not in canvas or "height" not in canvas:
        raise SpecError("design spec requires canvas.width and canvas.height")
    try:
        w, h = int(canvas["width"]), int(canvas["height"])
    except (TypeError, ValueError) as exc:
        raise SpecError(f"canvas.width/height must be integers: {exc}") from exc
    if w <= 0 or h <= 0:
        raise SpecError(f"canvas dimensions must be positive, got {w}x{h}")

    ctype = spec.get("creative_type", DEFAULT_CREATIVE_TYPE)
    if ctype not in CREATIVE_TYPES:
        raise SpecError(f"unknown creative_type {ctype!r}; expected one of {sorted(CREATIVE_TYPES)}")

    cand = spec.get("candidate")
    if cand is not None and cand not in CANDIDATES:
        raise SpecError(f"unknown candidate {cand!r}; expected one of {sorted(CANDIDATES)}")

    margin = spec.get("margin", DEFAULT_MARGIN)
    if not isinstance(margin, (int, float)) or not 0 <= margin < 0.3:
        raise SpecError(f"margin must be a fraction in [0, 0.3), got {margin!r}")

    elements = spec.get("elements", {})
    if not isinstance(elements, dict):
        raise SpecError("elements must be an object keyed by element name")
    for name, cfg in elements.items():
        if cfg is None:
            continue
        if not isinstance(cfg, dict):
            raise SpecError(f"elements.{name} must be an object, got {type(cfg).__name__}")
        if "area" in cfg:
            normalize_area(cfg["area"])  # raises with a good message
        for key in ("x", "y", "w", "h", "width", "max_width", "height"):
            if key in cfg and not isinstance(cfg[key], (int, float)):
                raise SpecError(f"elements.{name}.{key} must be a number, got {cfg[key]!r}")
            if key in cfg and not -0.5 <= float(cfg[key]) <= 1.5:
                raise SpecError(
                    f"elements.{name}.{key}={cfg[key]} is out of range — these are "
                    "normalized fractions of the canvas (0..1), not pixels"
                )

    subj = spec.get("subject", {})
    if subj and "coverage" in subj:
        cov = subj["coverage"]
        if not isinstance(cov, (int, float)) or not 0 < cov <= 1:
            raise SpecError(f"subject.coverage must be a fraction in (0, 1], got {cov!r}")

    return spec


def save_spec(spec: dict, path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as fh:
        json.dump(spec, fh, ensure_ascii=False, indent=2)
    return p


def layout_report(spec: dict) -> dict:
    """Everything a caller needs to decide whether this plan is worth paying an
    image-generation call for."""
    planned = resolve_layout(spec)
    adjusted, moves = resolve_collisions(spec, planned)
    issues = validate_layout(spec, adjusted)
    return {
        "boxes": {k: [round(x, 4) for x in v.as_tuple()] for k, v in adjusted.items()},
        "moves": moves,
        "issues": [i.to_dict() for i in issues],
        "errors": sum(1 for i in issues if i.severity == "error"),
        "warnings": sum(1 for i in issues if i.severity == "warning"),
        "negative_space": negative_space_regions(spec, adjusted),
    }


def main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(description="Validate a Design Spec and print its resolved layout.")
    p.add_argument("spec", help="Path to a design-spec JSON file")
    p.add_argument("--json", action="store_true", help="Emit the report as JSON")
    args = p.parse_args(argv)

    try:
        spec = load_spec(args.spec)
    except SpecError as exc:
        print(f"INVALID: {exc}")
        return 2

    report = layout_report(spec)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"creative_type: {spec['creative_type']}  candidate: {spec.get('candidate')}")
        print(f"canvas: {spec['canvas']['width']}x{spec['canvas']['height']}")
        for name, box in sorted(report["boxes"].items()):
            print(f"  {name:<10} x={box[0]:.3f} y={box[1]:.3f} w={box[2]:.3f} h={box[3]:.3f}")
        for move in report["moves"]:
            print(f"  auto-fix: {move}")
        for issue in report["issues"]:
            print(f"  [{issue['severity'].upper()}] {issue['element']}: {issue['message']}")
            if issue["correction"]:
                print(f"            -> {issue['correction']}")
        print(f"{report['errors']} error(s), {report['warnings']} warning(s)")
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
