#!/usr/bin/env python3
"""
Design Spec -> image-generation prompt.

This is the separation the old workflow was missing. Art direction (what is
where, how big, what outranks what) is decided in the Design Spec. This module
only *translates* it — it makes no layout decisions of its own, which is why
the photograph and the composite can no longer disagree about where the empty
space is.

The "keep this region quiet" clauses are computed from the resolved layout
boxes, not written by hand. Move the headline in the spec and the prompt's
reserved region moves with it.

Brand-agnostic: every aesthetic noun comes from the brand profile's
`photography` block.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from design_spec import (
    Box,
    SpecError,
    load_brand_profile,
    load_spec,
    negative_space_regions,
    resolve_collisions,
    resolve_layout,
    resolve_subject_box,
)

AREA_PROSE = {
    "upper_left": "upper-left",
    "upper_center": "upper-centre",
    "upper_right": "upper-right",
    "mid_left": "centre-left",
    "center": "centre",
    "mid_right": "centre-right",
    "lower_left": "lower-left",
    "lower_center": "lower-centre",
    "lower_right": "lower-right",
}

CAMERA_PROSE = {
    "directly_overhead": "shot from directly overhead, flat-lay",
    "slight_overhead": "slight overhead angle, roughly 30-45 degrees above the surface",
    "three_quarter": "three-quarter angle, low enough to show depth in the cut",
    "eye_level": "eye level with the surface",
}

CROP_PROSE = {
    "tight": "crop tightly around the subject so it fills the frame",
    "medium": "crop moderately — the subject dominates but the working surface reads around it",
    "wide": "wider crop with the working environment clearly visible around the subject",
}

ENVIRONMENT_PROSE = {
    "minimal": "keep the surrounding environment minimal and uncluttered",
    "present": "show enough of the real working environment to read as authentic",
    "rich": "the working environment is part of the story — show it in context",
}

ELEMENT_PROSE = {
    "headline": "a compact text label",
    "subtext": "a short supporting line",
    "cta": "a button",
    "badge": "a round badge",
    "logo": "a small logo mark",
    "footer": "a small contact line",
    "bullets": "a short list",
    "watermark": "a faint watermark",
}


def _coverage_band(area: float) -> str:
    """Image models respond to a range far better than a decimal."""
    pct = area * 100
    low, high = max(5, int(pct) - 5), min(95, int(pct) + 5)
    return f"{low}-{high}%"


def _region_clause(region: dict, canvas_ratio: float) -> str | None:
    box = Box(*region["box"])
    what = ELEMENT_PROSE.get(region["for"], "an overlay element")
    where = AREA_PROSE.get(region["area"], region["area"].replace("_", "-"))
    # Regions too small to matter to a photographer aren't worth a clause;
    # a prompt full of trivial constraints dilutes the ones that count.
    if box.area < 0.015:
        return None
    return (
        f"The {where} region (roughly x {box.x:.2f}-{box.x1:.2f}, y {box.y:.2f}-{box.y1:.2f} "
        f"of the frame) must stay visually quiet and low-detail — {what} will be "
        f"composited there afterwards."
    )


def build_image_prompt(spec: dict, brand_profile: dict) -> str:
    """Render a Design Spec into an image-generation prompt.

    Deterministic: the same spec and profile always produce the same text, so a
    revision that changes one thing produces a prompt that differs in exactly
    that thing.
    """
    photo = brand_profile.get("photography", {})
    subject = spec.get("subject", {})
    comp = spec.get("composition", {})

    planned = resolve_layout(spec)
    adjusted, _ = resolve_collisions(spec, planned)
    subj_box = resolve_subject_box(spec)
    regions = negative_space_regions(spec, adjusted)

    canvas = spec["canvas"]
    ratio = canvas["width"] / canvas["height"]

    lines: list[str] = []

    genre = photo.get("genre", "photograph")
    lines.append(f"{genre[0].upper()}{genre[1:]}.")
    lines.append("")

    # --- subject ------------------------------------------------------------
    desc = subject.get("description") or subject.get("type") or "the product"
    lines.append(f"Primary focal subject: {desc}.")

    where = AREA_PROSE.get(subject.get("area", "center"), "centre")
    lines.append(
        f"Place the subject toward the {where} of the frame, centred near "
        f"x {subj_box.center[0]:.2f}, y {subj_box.center[1]:.2f}, and make it clearly "
        f"dominant — it should occupy roughly {_coverage_band(subj_box.area)} of the "
        f"frame's visual area."
    )
    lines.append("")

    # --- camera / crop / environment ---------------------------------------
    lines.append(
        "Camera: "
        + CAMERA_PROSE.get(comp.get("camera", "slight_overhead"), comp.get("camera", ""))
        + "."
    )
    for phrase in (CROP_PROSE.get(comp.get("crop", "tight"), ""),
                   ENVIRONMENT_PROSE.get(comp.get("environment_weight", "present"), "")):
        if phrase:
            lines.append(phrase[0].upper() + phrase[1:] + ".")
    lines.append("")

    # --- reserved negative space (derived from the resolved layout) ---------
    clauses = [c for c in (_region_clause(r, ratio) for r in regions) if c]
    if clauses:
        lines.append("Reserved areas — compose around these:")
        lines.extend(clauses)
        lines.append(
            "Do not place the subject, a bright highlight or a busy pattern in those regions."
        )
        lines.append("")

    # --- brand photography direction ---------------------------------------
    if photo.get("lighting"):
        lines.append(f"Lighting: {photo['lighting']}.")
    if photo.get("environment"):
        lines.append(f"Environment: {photo['environment']}.")
    if photo.get("color_mood"):
        lines.append(f"Colour: {photo['color_mood']}.")
    if photo.get("hands"):
        lines.append(f"If hands appear: {photo['hands']}.")
    if photo.get("props"):
        lines.append(f"Props: {photo['props']}.")
    if photo.get("realism"):
        lines.append(f"Realism: {photo['realism']}.")
    lines.append("")

    # --- hard exclusions ----------------------------------------------------
    avoid = list(photo.get("avoid", [])) + list(spec.get("avoid", []))
    seen, ordered = set(), []
    for item in avoid:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    if ordered:
        lines.append("Must not appear in the image:")
        for item in ordered:
            lines.append(f"- {item}")
        lines.append("")

    lines.append(
        "The frame must be edge-to-edge photography at "
        f"{canvas['width']}x{canvas['height']} — no borders, no blank bands, no letterboxing."
    )

    return "\n".join(lines).strip()


def build_revision_prompt(spec: dict, brand_profile: dict, corrections: list[str]) -> str:
    """A revision prompt is the base prompt plus the critic's actual
    corrections, appended as explicit instructions. Regenerating from a
    from-scratch prompt loses whatever the previous image got right."""
    base = build_image_prompt(spec, brand_profile)
    if not corrections:
        return base
    lines = [base, "", "Corrections to apply versus the previous attempt:"]
    lines.extend(f"- {c}" for c in corrections)
    return "\n".join(lines)


def prompt_bundle(spec: dict, brand_profile: dict) -> dict:
    """Everything an image tool might need, including the negative prompt for
    tools that take one separately."""
    return {
        "prompt": build_image_prompt(spec, brand_profile),
        "negative_prompt": brand_profile.get("photography", {}).get("negative_prompt", ""),
        "width": spec["canvas"]["width"],
        "height": spec["canvas"]["height"],
        "aspect": spec["canvas"].get("aspect"),
        "candidate": spec.get("candidate"),
        "creative_type": spec.get("creative_type"),
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("spec", help="Path to a design-spec JSON file")
    p.add_argument("--brand-profile", required=True, help="Path to the brand profile JSON")
    p.add_argument("--json", action="store_true", help="Emit the full bundle as JSON")
    p.add_argument("--revision", nargs="*", default=None, help="Correction lines to append")
    args = p.parse_args(argv)

    try:
        spec = load_spec(args.spec)
        profile = load_brand_profile(args.brand_profile)
    except SpecError as exc:
        print(f"ERROR: {exc}")
        return 2

    if args.json:
        bundle = prompt_bundle(spec, profile)
        if args.revision:
            bundle["prompt"] = build_revision_prompt(spec, profile, args.revision)
        print(json.dumps(bundle, ensure_ascii=False, indent=2))
    else:
        if args.revision:
            print(build_revision_prompt(spec, profile, args.revision))
        else:
            print(build_image_prompt(spec, profile))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
