"""Quality gate: automated defect measurement, scoring, routing, revision limit."""
import json
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import design_spec as ds  # noqa: E402
import review as rv  # noqa: E402

W, H = 540, 675


def noisy(w=W, h=H, seed=0, base=120, spread=60):
    """A stand-in photograph: textured enough that a flat band is detectable."""
    rng = np.random.default_rng(seed)
    arr = rng.integers(base - spread, base + spread, size=(h, w, 3), dtype=np.int16)
    return Image.fromarray(arr.astype(np.uint8), "RGB")


def with_white_band(img, fraction=0.18):
    out = img.copy()
    ImageDraw.Draw(out).rectangle((0, 0, out.width, int(out.height * fraction)), fill=(255, 255, 255))
    return out


# --------------------------------------------------------------------------
# Dead-band detection — the v2 background failure
# --------------------------------------------------------------------------


def test_flat_white_band_is_detected():
    problems = rv.detect_dead_bands(with_white_band(noisy()))
    assert problems
    assert problems[0].category == "photography"
    assert problems[0].route == "regenerate_image"
    assert "top" in problems[0].issue


def test_flat_black_band_is_detected():
    img = noisy()
    ImageDraw.Draw(img).rectangle((0, int(img.height * 0.9), img.width, img.height), fill=(0, 0, 0))
    problems = rv.detect_dead_bands(img)
    assert any("bottom" in p.issue for p in problems)


def test_clean_photograph_has_no_dead_bands():
    assert rv.detect_dead_bands(noisy()) == []


def test_a_band_too_thin_to_matter_is_ignored():
    assert rv.detect_dead_bands(with_white_band(noisy(), fraction=0.01)) == []


# --------------------------------------------------------------------------
# Element contrast — the invisible-logo failure
# --------------------------------------------------------------------------


def test_invisible_element_is_detected():
    """A logo composited onto a backing disc of nearly the same tone as the
    photo leaves its region unchanged — it did not survive the composite."""
    background = noisy()
    composite = background.copy()  # nothing was actually drawn
    boxes = {"logo": ds.Box(0.8, 0.04, 0.13, 0.10)}
    problems = rv.measure_element_contrast(composite, background, boxes)
    assert problems and problems[0].element == "logo"
    assert problems[0].route == "recomposite"


def test_visible_element_passes():
    background = noisy()
    composite = background.copy()
    ImageDraw.Draw(composite).rectangle((int(0.8 * W), int(0.04 * H), int(0.93 * W), int(0.14 * H)),
                                        fill=(255, 0, 0))
    boxes = {"logo": ds.Box(0.8, 0.04, 0.13, 0.10)}
    assert rv.measure_element_contrast(composite, background, boxes) == []


def test_contrast_check_is_skipped_without_a_background():
    assert rv.measure_element_contrast(noisy(), None, {"logo": ds.Box(0, 0, 0.2, 0.2)}) == []


def test_contrast_check_resizes_a_mismatched_background():
    background = noisy(w=W * 2, h=H * 2)
    composite = noisy(seed=1)
    boxes = {"cta": ds.Box(0.3, 0.85, 0.4, 0.06)}
    rv.measure_element_contrast(composite, background, boxes)  # must not raise


# --------------------------------------------------------------------------
# Thumbnail test
# --------------------------------------------------------------------------


def test_thumbnail_is_written(tmp_path):
    boxes = {"subject": ds.Box(0.1, 0.2, 0.8, 0.6)}
    _, path = rv.thumbnail_test(noisy(), boxes, tmp_path / "t" / "thumb.png")
    assert path.exists()
    assert Image.open(path).width == rv.THUMBNAIL_WIDTH


def test_element_that_vanishes_at_thumbnail_size_is_flagged():
    flat = Image.new("RGB", (W, H), (128, 128, 128))
    boxes = {"subject": ds.Box(0.1, 0.1, 0.8, 0.6), "headline": ds.Box(0.05, 0.05, 0.4, 0.1)}
    problems, _ = rv.thumbnail_test(flat, boxes, None)
    assert any(p.category == "legibility" for p in problems)


def test_sub_pixel_element_is_flagged_as_disappearing():
    boxes = {"cta": ds.Box(0.5, 0.5, 0.001, 0.001), "subject": ds.Box(0.1, 0.1, 0.8, 0.6)}
    problems, _ = rv.thumbnail_test(noisy(), boxes, None)
    assert any("disappears in feed" in p.issue for p in problems)


def test_uniform_visual_weight_is_flagged_as_no_hierarchy():
    """Everything equally busy at thumbnail size means nothing leads the eye."""
    img = noisy(seed=3)
    boxes = {
        "subject": ds.Box(0.1, 0.1, 0.5, 0.4),
        "headline": ds.Box(0.1, 0.6, 0.5, 0.1),
        "cta": ds.Box(0.3, 0.8, 0.4, 0.06),
    }
    problems, _ = rv.thumbnail_test(img, boxes, None)
    assert any(p.category == "hierarchy" for p in problems)


# --------------------------------------------------------------------------
# Subject prominence
# --------------------------------------------------------------------------


def test_subject_buried_in_a_busy_background_is_flagged():
    img = Image.fromarray(
        np.random.default_rng(5).integers(0, 255, size=(H, W, 3), dtype=np.uint8), "RGB")
    # Declared subject region is flat — all the detail is everywhere else.
    ImageDraw.Draw(img).rectangle((int(0.2 * W), int(0.2 * H), int(0.8 * W), int(0.8 * H)),
                                  fill=(120, 120, 120))
    problems = rv.estimate_subject_prominence(img, {"subject": ds.Box(0.2, 0.2, 0.6, 0.6)})
    assert problems and problems[0].route == "revise_spec"
    assert "focal point" in problems[0].issue


def test_prominent_subject_passes():
    img = Image.new("RGB", (W, H), (110, 110, 110))
    arr = np.array(img)
    rng = np.random.default_rng(7)
    y0, y1 = int(0.2 * H), int(0.8 * H)
    x0, x1 = int(0.2 * W), int(0.8 * W)
    arr[y0:y1, x0:x1] = rng.integers(0, 255, size=(y1 - y0, x1 - x0, 3), dtype=np.uint8)
    problems = rv.estimate_subject_prominence(Image.fromarray(arr, "RGB"),
                                              {"subject": ds.Box(0.2, 0.2, 0.6, 0.6)})
    assert problems == []


def test_prominence_check_needs_a_subject_box():
    assert rv.estimate_subject_prominence(noisy(), {}) == []


# --------------------------------------------------------------------------
# Scoring
# --------------------------------------------------------------------------


def test_clean_creative_scores_100_and_passes():
    result = rv.score([])
    assert result["score"] == 100
    assert result["decision"] == "PASS"
    assert result["next_action"] == "none"
    assert result["passed"] is True


def test_rubric_sums_to_100():
    assert sum(rv.RUBRIC.values()) == 100
    assert sum(rv.score([])["breakdown"].values()) == 100


def test_severity_scales_the_deduction():
    high = rv.score([rv.Problem("composition", "high", "x", "y")])["score"]
    low = rv.score([rv.Problem("composition", "low", "x", "y")])["score"]
    assert high < low < 100


def test_decision_bands():
    assert rv.score([])["decision"] == "PASS"

    # One medium defect is the "good — minor improvements optional" band.
    minor = rv.score([rv.Problem("composition", "medium", "i", "c")])
    assert rv.PASS_THRESHOLD <= minor["score"] < rv.PASS_EXCELLENT
    assert minor["decision"] == "PASS"

    # Two mediums drop below the ship threshold.
    assert rv.score([rv.Problem("composition", "medium", "i", "c"),
                     rv.Problem("hierarchy", "medium", "i", "c")])["decision"] == "REVISE"

    many = rv.score([rv.Problem("composition", "high", "i", "c"),
                     rv.Problem("photography", "high", "i", "c"),
                     rv.Problem("typography", "high", "i", "c"),
                     rv.Problem("hierarchy", "high", "i", "c")])
    assert many["decision"] == "REJECT"


def test_a_single_high_severity_defect_blocks_the_ship():
    """The regression guard for how the broken render passed: a flat white band
    across 18% of the frame scored 95/100 under pure arithmetic. A defect a
    viewer would notice must not ship on a good average."""
    result = rv.score([rv.Problem("photography", "high",
                                  "flat white band along the top edge", "regenerate full-bleed")])
    assert result["score"] >= rv.PASS_THRESHOLD, "arithmetic alone would have passed this"
    assert result["decision"] == "REVISE"
    assert result["passed"] is False


def test_a_category_cannot_go_negative():
    """One catastrophic area must not drag the total below what the other
    categories genuinely earned."""
    problems = [rv.Problem("photography", "high", "i", "c") for _ in range(10)]
    result = rv.score(problems)
    assert result["breakdown"]["photography_realism"] == 0
    assert result["score"] >= 0
    assert result["breakdown"]["brand_consistency"] == rv.RUBRIC["brand_consistency"]


def test_score_accepts_dicts_as_well_as_problems():
    result = rv.score([{"category": "typography", "severity": "high",
                        "issue": "i", "correction": "c"}])
    assert result["score"] < 100


# --------------------------------------------------------------------------
# Failure routing — photography vs composition vs compositor
# --------------------------------------------------------------------------


def test_photography_failure_routes_to_image_regeneration():
    result = rv.score([rv.Problem("photography", "high", "fake-looking meat", "regenerate")])
    assert result["next_action"] == "regenerate_image"


def test_layout_failure_routes_to_a_recomposite_not_a_new_image():
    """The money-saving rule: a badly placed label must not trigger a fresh
    paid image generation."""
    result = rv.score([rv.Problem("collision", "high", "badge overlaps CTA", "move the badge")])
    assert result["next_action"] == "recomposite"


def test_composition_failure_routes_to_a_spec_revision():
    result = rv.score([rv.Problem("hierarchy", "high", "product too small", "raise coverage")])
    assert result["next_action"] == "revise_spec"


def test_photography_wins_when_several_stages_are_implicated():
    """If the photo itself is wrong, fixing the layout first is wasted work."""
    result = rv.score([
        rv.Problem("collision", "high", "i", "c"),
        rv.Problem("photography", "high", "i", "c"),
    ])
    assert result["next_action"] == "regenerate_image"


def test_low_severity_problems_do_not_drive_routing():
    result = rv.score([rv.Problem("photography", "low", "i", "c")])
    assert result["next_action"] != "regenerate_image"


# --------------------------------------------------------------------------
# Actionable feedback
# --------------------------------------------------------------------------


def test_corrections_are_returned_for_the_chosen_route():
    problems = [
        rv.Problem("photography", "high", "lighting reads as restaurant", "use cooler fluorescent lighting"),
        rv.Problem("collision", "high", "badge on CTA", "move the badge up"),
    ]
    result = rv.score(problems)
    assert result["corrections"] == ["use cooler fluorescent lighting"]


def test_corrections_are_ordered_by_severity():
    problems = [
        rv.Problem("collision", "low", "minor", "fix minor"),
        rv.Problem("collision", "high", "major", "fix major"),
    ]
    assert rv.score(problems)["corrections"][0] == "fix major"


def test_every_problem_carries_a_correction_and_a_route():
    for prob in rv.score([rv.Problem("typography", "high", "i", "c")])["problems"]:
        assert prob["correction"]
        assert prob["route"] in rv.ROUTE_ORDER


# --------------------------------------------------------------------------
# Revision limit
# --------------------------------------------------------------------------


def test_revision_budget_counts_down():
    failing = [rv.Problem("composition", "high", "i", "c")]
    assert rv.score(failing, revision=0)["revisions_remaining"] == 2
    assert rv.score(failing, revision=1)["revisions_remaining"] == 1


def test_exhausted_budget_stops_instead_of_looping():
    failing = [rv.Problem("composition", "high", "i", "c")]
    result = rv.score(failing, revision=rv.MAX_REVISIONS)
    assert result["next_action"] == "stop_below_threshold"
    assert result["below_threshold_final"] is True
    assert result["passed"] is False


def test_a_pass_at_the_budget_limit_is_still_a_pass():
    result = rv.score([], revision=rv.MAX_REVISIONS)
    assert result["passed"] is True
    assert result["below_threshold_final"] is False


def test_custom_revision_budget_is_respected():
    result = rv.score([rv.Problem("composition", "high", "i", "c")], revision=1, max_revisions=1)
    assert result["next_action"] == "stop_below_threshold"


# --------------------------------------------------------------------------
# End-to-end inspection
# --------------------------------------------------------------------------


def test_inspect_reports_measured_geometry_problems(tmp_path):
    """Geometry is re-checked against what was ACTUALLY drawn, not the plan."""
    img = noisy()
    path = tmp_path / "c.png"
    img.save(path)
    spec = ds.build_spec()
    manifest = {"boxes": {"logo": [0.3, 0.3, 0.45, 0.3], "subject": [0.1, 0.1, 0.8, 0.8]}}
    result = rv.inspect(path, manifest=manifest, spec=spec)
    categories = {p["category"] for p in result["problems"]}
    assert "proportion" in categories  # logo far over its width limit


def test_review_merges_reviewer_findings_with_measurements(tmp_path):
    path = tmp_path / "c.png"
    with_white_band(noisy()).save(path)
    findings = [{"category": "brand_consistency", "severity": "high",
                 "issue": "gloves are the wrong colour", "correction": "use black nitrile gloves"}]
    result = rv.review(path, reviewer_findings=findings, thumbnail_path=tmp_path / "t.png")
    sources = {p["source"] for p in result["problems"]}
    assert sources == {"automated", "reviewer"}
    assert result["decision"] != "PASS"
    assert Path(result["thumbnail"]).exists()


def test_review_of_a_clean_render_passes(tmp_path):
    path = tmp_path / "c.png"
    noisy().save(path)
    result = rv.review(path)
    assert result["passed"] is True


def test_cli_exit_code_reflects_the_decision(tmp_path, capsys):
    good, bad = tmp_path / "good.png", tmp_path / "bad.png"
    noisy().save(good)
    with_white_band(noisy()).save(bad)
    assert rv.main([str(good)]) == 0
    assert rv.main([str(bad)]) == 1
    assert "score" in capsys.readouterr().out


def test_cli_accepts_a_manifest_and_findings_file(tmp_path):
    path = tmp_path / "c.png"
    noisy().save(path)
    manifest = tmp_path / "m.json"
    manifest.write_text(json.dumps({"boxes": {"subject": [0.1, 0.1, 0.8, 0.7]}}), encoding="utf-8")
    findings = tmp_path / "f.json"
    findings.write_text(json.dumps({"problems": [
        {"category": "composition", "severity": "high", "issue": "i", "correction": "c"}]}),
        encoding="utf-8")
    assert rv.main([str(path), "--manifest", str(manifest), "--findings", str(findings), "--json"]) == 1


# --------------------------------------------------------------------------
# Interior dead bands and graphic coverage — the defects that actually shipped
# --------------------------------------------------------------------------


def band_in_middle(img, y0=0.22, y1=0.29, tone=(234, 234, 234)):
    out = img.copy()
    ImageDraw.Draw(out).rectangle(
        (0, int(out.height * y0), out.width, int(out.height * y1)), fill=tone)
    return out


def test_interior_dead_band_is_detected():
    """The shipped v2 render's white band sat between the banner and the photo,
    so an edge-inward scan never reached it."""
    problems = rv.detect_dead_bands(band_in_middle(noisy()))
    assert problems
    assert problems[0].route == "regenerate_image"
    assert "middle of the frame" in problems[0].issue


def test_off_white_padding_is_detected():
    """JPEG never returns exact white — the real band measured 234, and a
    brightness cutoff at 235 let it through."""
    assert rv.detect_dead_bands(band_in_middle(noisy(), tone=(234, 234, 234)))


def test_a_coloured_band_is_not_treated_as_padding():
    """A brand banner is a composition choice, not generator padding — it must
    route to the layout, not to a paid image regeneration."""
    branded = band_in_middle(noisy(), tone=(185, 15, 42))
    assert rv.detect_dead_bands(branded) == []


def test_graphic_coverage_flags_a_template_looking_creative():
    img = noisy()
    ImageDraw.Draw(img).rectangle((0, 0, img.width, int(img.height * 0.30)), fill=(185, 15, 42))
    problems = rv.measure_graphic_coverage(img)
    assert problems and problems[0].category == "composition"
    assert "edge-to-edge" in problems[0].correction


def test_graphic_coverage_passes_a_full_bleed_photograph():
    assert rv.measure_graphic_coverage(noisy()) == []


def test_graphic_coverage_ignores_a_tiny_image():
    assert rv.measure_graphic_coverage(Image.new("RGB", (2, 2))) == []


def test_inspect_marks_a_manifest_free_run_as_partial(tmp_path):
    """A score with no manifest covers photography only — it must not read as a
    clean bill of health."""
    path = tmp_path / "c.png"
    noisy().save(path)
    assert rv.inspect(path)["partial"] is True
    assert rv.inspect(path, manifest={"boxes": {"subject": [0.1, 0.1, 0.8, 0.7]}})["partial"] is False


# --------------------------------------------------------------------------
# Calibration against this workspace's real creatives
# --------------------------------------------------------------------------

REFERENCES = Path(__file__).parents[4] / "social" / "_references"
CREATIVES = Path(__file__).parents[4] / "social" / "creatives"


@pytest.mark.skipif(not REFERENCES.exists(), reason="reference creatives not present")
@pytest.mark.parametrize("name", ["1.png", "2.png", "3.png"])
def test_brand_reference_creatives_pass_the_gate(name):
    """The gate is calibrated against the brand's own published work. If it
    fails these, its thresholds are wrong, not the creatives."""
    ref = REFERENCES / name
    if not ref.exists():
        pytest.skip(f"{name} not present")
    result = rv.review(ref)
    assert result["passed"], [p["issue"] for p in result["problems"]]


@pytest.mark.skipif(not CREATIVES.exists(), reason="rendered creatives not present")
def test_the_previously_shipped_broken_renders_are_caught():
    """Regression guard against the exact outputs that shipped before this
    pipeline existed: a padded background and a banner eating the frame."""
    broken = [
        CREATIVES / "2026-09-06-lahma-3alena-shawi-3alek-v2" / "slide-1-hook.png",
        CREATIVES / "2026-09-06-sofret-ramadan" / "ad-4x5-hook-a-convenience.png",
    ]
    for path in broken:
        if not path.exists():
            pytest.skip(f"{path.name} not present")
        result = rv.review(path)
        assert not result["passed"], f"{path.name} should not pass the gate"
        assert result["corrections"], f"{path.name} produced no actionable correction"


def test_explicit_stage_overrides_the_category_route():
    """'brand_consistency' covers both a wrong brand red (compositor) and
    wrong-coloured gloves (only a regeneration fixes that). An explicit stage
    keeps the correction attached to the step that can act on it."""
    default = rv.Problem("brand_consistency", "high", "wrong red", "use the brand red")
    assert default.route == "recomposite"

    photographic = rv.Problem("brand_consistency", "high", "white gloves, should be black nitrile",
                              "regenerate with black nitrile gloves", stage="regenerate_image")
    assert photographic.route == "regenerate_image"

    result = rv.score([photographic])
    assert result["next_action"] == "regenerate_image"
    assert "regenerate with black nitrile gloves" in result["corrections"]


def test_stage_survives_a_dict_finding():
    result = rv.score([{"category": "brand_consistency", "severity": "high", "issue": "i",
                        "correction": "c", "stage": "regenerate_image"}])
    assert result["next_action"] == "regenerate_image"


def test_an_invalid_stage_falls_back_to_the_category_route():
    p = rv.Problem("collision", "high", "i", "c", stage="teleport")
    assert p.route == "recomposite"


def test_corrections_are_deduplicated():
    same = [rv.Problem("collision", "high", "a", "move the badge"),
            rv.Problem("collision", "medium", "b", "move the badge")]
    assert rv.score(same)["corrections"] == ["move the badge"]
