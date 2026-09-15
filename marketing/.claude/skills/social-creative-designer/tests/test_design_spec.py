"""Design Spec: schema validation, layout defaults, geometry, collisions."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import design_spec as ds  # noqa: E402


# --------------------------------------------------------------------------
# Geometry primitives
# --------------------------------------------------------------------------


def test_box_area_and_intersection():
    a = ds.Box(0.0, 0.0, 0.5, 0.5)
    b = ds.Box(0.25, 0.25, 0.5, 0.5)
    assert a.area == pytest.approx(0.25)
    assert a.intersection(b).area == pytest.approx(0.0625)
    assert a.overlap_ratio(b) == pytest.approx(0.25)


def test_disjoint_boxes_do_not_overlap():
    a = ds.Box(0.0, 0.0, 0.2, 0.2)
    b = ds.Box(0.5, 0.5, 0.2, 0.2)
    assert a.intersection(b).area == 0.0
    assert a.overlap_ratio(b) == 0.0


def test_overlap_ratio_is_asymmetric():
    """A small badge fully inside a large product is 100% blocked; the product
    is barely touched. Those are different problems and must score differently."""
    big = ds.Box(0.0, 0.0, 0.8, 0.8)
    small = ds.Box(0.1, 0.1, 0.1, 0.1)
    assert small.overlap_ratio(big) == pytest.approx(1.0)
    assert big.overlap_ratio(small) < 0.03


def test_clamp_into_slides_without_resizing():
    frame = ds.Box(0.05, 0.05, 0.9, 0.9)
    box = ds.Box(-0.2, 0.5, 0.3, 0.1)
    clamped = box.clamp_into(frame)
    assert clamped.x == pytest.approx(0.05)
    assert clamped.w == pytest.approx(0.3)


def test_to_pixels_rounds():
    assert ds.Box(0.1, 0.2, 0.5, 0.25).to_pixels(1080, 1350) == (108, 270, 540, 338)


# --------------------------------------------------------------------------
# Areas
# --------------------------------------------------------------------------


def test_area_aliases_normalize():
    assert ds.normalize_area("tr") == "upper_right"
    assert ds.normalize_area("bottom_center") == "lower_center"
    assert ds.normalize_area("  Upper_Left ") == "upper_left"


def test_unknown_area_raises_with_guidance():
    with pytest.raises(ds.SpecError) as exc:
        ds.normalize_area("middle_of_nowhere")
    assert "unknown area" in str(exc.value)


def test_area_to_corner_maps_to_compositor_vocabulary():
    assert ds.area_to_corner("upper_right") == "tr"
    assert ds.area_to_corner("lower_left") == "bl"
    assert ds.area_to_corner("bl") == "bl"


def test_place_respects_margin_on_each_edge():
    box = ds.place("lower_right", 0.2, 0.1, margin=0.05)
    assert box.x1 == pytest.approx(0.95)
    assert box.y1 == pytest.approx(0.95)
    box = ds.place("upper_left", 0.2, 0.1, margin=0.05)
    assert (box.x, box.y) == (pytest.approx(0.05), pytest.approx(0.05))


def test_place_centers_on_center_areas():
    box = ds.place("lower_center", 0.4, 0.06, margin=0.045)
    assert box.center[0] == pytest.approx(0.5)


# --------------------------------------------------------------------------
# Spec construction and defaults
# --------------------------------------------------------------------------


def test_build_spec_uses_creative_type_defaults():
    spec = ds.build_spec(creative_type="hero_offer")
    assert spec["canvas"] == {"width": 1080, "height": 1350, "aspect": "4:5"}
    assert spec["hierarchy"][0] == "subject"
    assert spec["elements"]["logo"]["area"] == "upper_right"


def test_build_spec_rejects_unknown_creative_type():
    with pytest.raises(ds.SpecError):
        ds.build_spec(creative_type="not_a_type")


def test_build_spec_rejects_unknown_aspect():
    with pytest.raises(ds.SpecError):
        ds.build_spec(aspect="7:3")


def test_candidates_are_genuinely_different_art_directions():
    """Not three rewordings — subject scale, crop and camera must all differ."""
    specs = [ds.build_spec(candidate=c) for c in ds.DEFAULT_CANDIDATES]
    coverages = {round(s["subject"]["coverage"], 3) for s in specs}
    cameras = {s["composition"]["camera"] for s in specs}
    assert len(coverages) == 3, "candidates must differ in subject scale"
    assert len(cameras) >= 2, "candidates must differ in camera angle"


def test_candidate_scales_the_creative_type_subject_budget():
    base = ds.build_spec(creative_type="hero_offer")["subject"]["coverage"]
    hero = ds.build_spec(creative_type="hero_offer", candidate="product_hero")
    doc = ds.build_spec(creative_type="hero_offer", candidate="documentary")
    assert hero["subject"]["coverage"] > base > doc["subject"]["coverage"]
    assert hero["composition"]["crop"] == "tight"


def test_candidate_cannot_exceed_the_creative_type_coverage_ceiling():
    spec = ds.build_spec(creative_type="value_list", candidate="product_hero")
    assert spec["subject"]["coverage"] <= ds.CREATIVE_TYPES["value_list"]["max_coverage"]


def test_locked_creative_type_keeps_its_subject_area():
    """value_list needs the upper copy band clear, so a candidate may not drag
    the subject back into the centre."""
    locked = ds.build_spec(creative_type="value_list", candidate="product_hero")
    assert locked["subject"]["area"] == "lower_center"
    unlocked = ds.build_spec(creative_type="hero_offer", candidate="commercial")
    assert unlocked["subject"]["area"] == "lower_right"


def test_brand_profile_calibration_overrides_preset():
    brand = {
        "colors": {"primary": "#000000"},
        "photography": {"avoid": ["faces"]},
        "layout_calibration": {"margin": 0.06, "elements": {"logo": {"width": 0.09}}},
    }
    spec = ds.build_spec(brand_profile=brand)
    assert spec["margin"] == pytest.approx(0.06)
    assert spec["elements"]["logo"]["width"] == pytest.approx(0.09)
    assert spec["avoid"] == ["faces"]


def test_explicit_overrides_beat_everything():
    brand = {"colors": {}, "photography": {}, "layout_calibration": {"elements": {"logo": {"width": 0.09}}}}
    spec = ds.build_spec(brand_profile=brand, overrides={"elements": {"logo": {"width": 0.15}}})
    assert spec["elements"]["logo"]["width"] == pytest.approx(0.15)


def test_deep_merge_keeps_untouched_sibling_keys():
    spec = ds.build_spec(overrides={"elements": {"headline": {"rotation": -8}}})
    assert spec["elements"]["headline"]["rotation"] == -8
    assert "max_width" in spec["elements"]["headline"]


# --------------------------------------------------------------------------
# Schema validation
# --------------------------------------------------------------------------


def test_validate_schema_accepts_a_built_spec():
    assert ds.validate_schema(ds.build_spec()) is not None


@pytest.mark.parametrize(
    "mutation, fragment",
    [
        ({"canvas": {"width": 1080}}, "canvas.width and canvas.height"),
        ({"canvas": {"width": 0, "height": 100}}, "must be positive"),
        ({"creative_type": "nope"}, "unknown creative_type"),
        ({"candidate": "nope"}, "unknown candidate"),
        ({"margin": 0.5}, "margin must be"),
        ({"margin": "wide"}, "margin must be"),
        ({"elements": {"cta": {"area": "outer_space"}}}, "unknown area"),
        ({"elements": {"cta": "bottom"}}, "must be an object"),
        ({"elements": {"cta": {"width": 540}}}, "normalized fractions"),
        ({"elements": {"cta": {"width": "wide"}}}, "must be a number"),
        ({"subject": {"coverage": 1.4}}, "subject.coverage"),
    ],
)
def test_validate_schema_rejects_bad_specs(mutation, fragment):
    spec = ds.build_spec()
    spec.update(mutation)
    with pytest.raises(ds.SpecError) as exc:
        ds.validate_schema(spec)
    assert fragment in str(exc.value)


def test_validate_schema_rejects_non_object():
    with pytest.raises(ds.SpecError):
        ds.validate_schema(["not", "a", "spec"])


def test_load_spec_reports_bad_json(tmp_path):
    p = tmp_path / "broken.json"
    p.write_text("{not json", encoding="utf-8")
    with pytest.raises(ds.SpecError) as exc:
        ds.load_spec(p)
    assert "not valid JSON" in str(exc.value)


def test_load_spec_reports_missing_file(tmp_path):
    with pytest.raises(ds.SpecError):
        ds.load_spec(tmp_path / "absent.json")


def test_save_and_load_roundtrip(tmp_path):
    spec = ds.build_spec(overrides={"elements": {"headline": {"text": "اللحمة علينا"}}})
    path = ds.save_spec(spec, tmp_path / "nested" / "spec.json")
    assert json.loads(path.read_text(encoding="utf-8"))["elements"]["headline"]["text"] == "اللحمة علينا"
    assert ds.load_spec(path)["creative_type"] == "hero_offer"


# --------------------------------------------------------------------------
# Layout resolution
# --------------------------------------------------------------------------


def test_resolve_layout_places_every_declared_element():
    spec = ds.build_spec()
    boxes = ds.resolve_layout(spec)
    for name in spec["elements"]:
        assert name in boxes


def test_disabled_elements_are_not_placed():
    spec = ds.build_spec(overrides={"elements": {"badge": {"enabled": False}}})
    assert "badge" not in ds.resolve_layout(spec)


def test_explicit_box_wins_over_area():
    spec = ds.build_spec(
        overrides={"elements": {"headline": {"x": 0.1, "y": 0.6, "w": 0.3, "h": 0.1}}}
    )
    box = ds.resolve_layout(spec)["headline"]
    assert (box.x, box.y, box.w, box.h) == pytest.approx((0.1, 0.6, 0.3, 0.1))


def test_measured_boxes_replace_planning_estimates():
    spec = ds.build_spec()
    measured = {"headline": ds.Box(0.5, 0.5, 0.1, 0.1)}
    assert ds.resolve_layout(spec, measured)["headline"].x == pytest.approx(0.5)


def test_subject_coverage_drives_subject_box_area():
    small = ds.resolve_subject_box(ds.build_spec(overrides={"subject": {"coverage": 0.30}}))
    large = ds.resolve_subject_box(ds.build_spec(overrides={"subject": {"coverage": 0.70}}))
    assert large.area > small.area
    assert small.area == pytest.approx(0.30, abs=0.05)


def test_explicit_subject_box_is_respected():
    spec = ds.build_spec(overrides={"subject": {"x": 0.2, "y": 0.3, "w": 0.5, "h": 0.4}})
    assert ds.resolve_subject_box(spec).as_tuple() == pytest.approx((0.2, 0.3, 0.5, 0.4))


# --------------------------------------------------------------------------
# Layout validation — the guards against the old failure modes
# --------------------------------------------------------------------------


def _categories(issues):
    return {(i.category, i.element) for i in issues}


def test_clean_default_layout_has_no_errors():
    for ctype in ds.CREATIVE_TYPES:
        spec = ds.build_spec(creative_type=ctype)
        boxes, _ = ds.resolve_collisions(spec, ds.resolve_layout(spec))
        errors = [i for i in ds.validate_layout(spec, boxes) if i.severity == "error"]
        assert not errors, f"{ctype} default layout has errors: {[e.message for e in errors]}"


def test_oversized_logo_is_an_error():
    spec = ds.build_spec(overrides={"elements": {"logo": {"width": 0.45}}})
    issues = ds.validate_layout(spec)
    assert ("proportion", "logo") in _categories(issues)


def test_oversized_cta_is_an_error():
    spec = ds.build_spec(overrides={"elements": {"cta": {"width": 0.9}}})
    assert ("proportion", "cta") in _categories(ds.validate_layout(spec))


def test_headline_spanning_the_canvas_is_an_error():
    spec = ds.build_spec(overrides={"elements": {"headline": {"max_width": 0.95}}})
    assert ("proportion", "headline") in _categories(ds.validate_layout(spec))


def test_tiny_subject_is_an_error():
    spec = ds.build_spec(overrides={"subject": {"coverage": 0.10}})
    issues = [i for i in ds.validate_layout(spec) if i.element == "subject"]
    assert issues and issues[0].severity == "error"


def test_element_outside_safe_area_is_an_error():
    spec = ds.build_spec(overrides={"elements": {"footer": {"x": 0.9, "y": 0.98, "w": 0.4, "h": 0.05}}})
    assert ("safe_area", "footer") in _categories(ds.validate_layout(spec))


def test_colliding_elements_are_reported_against_the_lower_priority_one():
    """badge and cta stacked on top of each other; cta outranks badge, so the
    badge is the one told to move."""
    spec = ds.build_spec(
        overrides={
            "elements": {
                "badge": {"x": 0.3, "y": 0.80, "w": 0.2, "h": 0.15},
                "cta": {"x": 0.3, "y": 0.80, "w": 0.4, "h": 0.06},
            }
        }
    )
    issues = [i for i in ds.validate_layout(spec) if i.category == "collision"]
    assert issues
    assert issues[0].element == "badge"
    assert "cta" in issues[0].correction


def test_headline_on_the_subject_is_a_collision():
    spec = ds.build_spec(
        overrides={
            "subject": {"x": 0.1, "y": 0.1, "w": 0.8, "h": 0.8},
            "elements": {"headline": {"x": 0.3, "y": 0.3, "w": 0.4, "h": 0.15}},
        }
    )
    issues = [i for i in ds.validate_layout(spec) if i.element == "headline"]
    assert any("covers" in i.message for i in issues)


def test_footer_over_the_subject_is_tolerated():
    """The contact line sits straight on the photo by design — it must not be
    reported as a collision the way a headline label would be."""
    spec = ds.build_spec(
        overrides={
            "subject": {"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0},
            "elements": {"footer": {"x": 0.05, "y": 0.90, "w": 0.5, "h": 0.03}},
        }
    )
    assert not [i for i in ds.validate_layout(spec) if i.element == "footer" and i.category == "collision"]


def test_logo_larger_than_headline_warns_about_hierarchy():
    spec = ds.build_spec(
        overrides={
            "elements": {
                "logo": {"x": 0.6, "y": 0.05, "w": 0.2, "h": 0.3},
                "headline": {"x": 0.05, "y": 0.5, "w": 0.2, "h": 0.05},
            }
        }
    )
    issues = [i for i in ds.validate_layout(spec) if i.element == "logo" and i.category == "hierarchy"]
    assert issues and issues[0].severity == "warning"


def test_issues_serialize_for_structured_feedback():
    spec = ds.build_spec(overrides={"elements": {"logo": {"width": 0.5}}})
    issue = ds.validate_layout(spec)[0].to_dict()
    assert set(issue) == {"severity", "category", "element", "message", "correction"}
    assert issue["correction"]


# --------------------------------------------------------------------------
# Collision resolution
# --------------------------------------------------------------------------


def test_resolve_collisions_separates_overlapping_elements():
    spec = ds.build_spec(
        overrides={
            "elements": {
                "badge": {"x": 0.30, "y": 0.80, "w": 0.20, "h": 0.12},
                "cta": {"x": 0.30, "y": 0.82, "w": 0.40, "h": 0.06},
            }
        }
    )
    before = ds.resolve_layout(spec)
    assert before["badge"].overlap_ratio(before["cta"]) > ds.OVERLAP_TOLERANCE
    after, log = ds.resolve_collisions(spec, before)
    assert after["badge"].overlap_ratio(after["cta"]) <= ds.OVERLAP_TOLERANCE
    assert any("badge" in entry for entry in log)


def test_resolve_collisions_moves_the_lower_priority_element():
    spec = ds.build_spec(
        overrides={
            "hierarchy": ["subject", "headline", "cta", "badge", "logo", "footer"],
            "elements": {
                "cta": {"x": 0.30, "y": 0.80, "w": 0.40, "h": 0.06},
                "badge": {"x": 0.32, "y": 0.80, "w": 0.20, "h": 0.12},
            },
        }
    )
    before = ds.resolve_layout(spec)
    after, _ = ds.resolve_collisions(spec, before)
    assert after["cta"].as_tuple() == pytest.approx(before["cta"].as_tuple())
    assert after["badge"].as_tuple() != pytest.approx(before["badge"].as_tuple())


def test_resolve_collisions_keeps_elements_inside_the_safe_frame():
    spec = ds.build_spec(
        overrides={
            "elements": {
                "cta": {"x": 0.05, "y": 0.88, "w": 0.40, "h": 0.06},
                "badge": {"x": 0.05, "y": 0.88, "w": 0.20, "h": 0.06},
            }
        }
    )
    after, _ = ds.resolve_collisions(spec, ds.resolve_layout(spec))
    frame = ds.safe_frame(spec)
    for name, box in after.items():
        if name == "subject":
            continue
        assert box.x >= frame.x - 1e-6 and box.y1 <= frame.y1 + 1e-6


def test_resolve_collisions_is_idempotent():
    spec = ds.build_spec()
    once, _ = ds.resolve_collisions(spec, ds.resolve_layout(spec))
    twice, log = ds.resolve_collisions(spec, once)
    assert not log
    for name in once:
        assert twice[name].as_tuple() == pytest.approx(once[name].as_tuple())


def test_resolve_collisions_terminates_on_an_impossible_layout():
    """Five big boxes in one corner cannot all be separated. It must return,
    not loop, and validate_layout must still report the truth."""
    spec = ds.build_spec(
        overrides={
            "elements": {
                name: {"x": 0.1, "y": 0.1, "w": 0.5, "h": 0.5}
                for name in ("headline", "cta", "badge", "logo", "footer")
            }
        }
    )
    after, _ = ds.resolve_collisions(spec, ds.resolve_layout(spec))
    assert len(after) >= 5
    assert any(i.category == "collision" for i in ds.validate_layout(spec, after))


# --------------------------------------------------------------------------
# Negative space — the layout/prompt link
# --------------------------------------------------------------------------


def test_negative_space_is_derived_from_resolved_boxes():
    spec = ds.build_spec()
    regions = ds.negative_space_regions(spec)
    assert {r["for"] for r in regions} == set(spec["elements"])
    assert all(len(r["box"]) == 4 for r in regions)


def test_negative_space_follows_the_headline_when_it_moves():
    """The regression guard for the original bug: the prompt's reserved area
    and the compositor's placement must not drift apart."""
    left = ds.build_spec(overrides={"elements": {"headline": {"area": "upper_left"}}})
    right = ds.build_spec(overrides={"elements": {"headline": {"area": "mid_right"}}})
    a = next(r for r in ds.negative_space_regions(left) if r["for"] == "headline")
    b = next(r for r in ds.negative_space_regions(right) if r["for"] == "headline")
    assert a["area"] != b["area"]
    assert a["box"][0] < b["box"][0]


def test_negative_space_is_ordered_by_hierarchy():
    spec = ds.build_spec()
    priorities = [r["priority"] for r in ds.negative_space_regions(spec)]
    assert priorities == sorted(priorities)


def test_nearest_area_names_the_right_third():
    assert ds.nearest_area(ds.Box(0.02, 0.02, 0.2, 0.1)) == "upper_left"
    assert ds.nearest_area(ds.Box(0.4, 0.88, 0.2, 0.06)) == "lower_center"
    assert ds.nearest_area(ds.Box(0.75, 0.45, 0.2, 0.1)) == "mid_right"


# --------------------------------------------------------------------------
# Report / CLI
# --------------------------------------------------------------------------


def test_layout_report_shape():
    report = ds.layout_report(ds.build_spec())
    assert set(report) == {"boxes", "moves", "issues", "errors", "warnings", "negative_space"}
    assert report["errors"] == 0


def test_layout_report_counts_errors():
    spec = ds.build_spec(overrides={"elements": {"logo": {"width": 0.5}}})
    assert ds.layout_report(spec)["errors"] >= 1


def test_cli_returns_nonzero_for_an_invalid_spec(tmp_path, capsys):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"canvas": {"width": 10}}), encoding="utf-8")
    assert ds.main([str(bad)]) == 2
    assert "INVALID" in capsys.readouterr().out


def test_cli_returns_zero_for_a_clean_spec(tmp_path):
    good = tmp_path / "good.json"
    ds.save_spec(ds.build_spec(), good)
    assert ds.main([str(good), "--json"]) == 0


# --------------------------------------------------------------------------
# Brand profile
# --------------------------------------------------------------------------


def test_brand_profile_missing_file_explains_itself(tmp_path):
    with pytest.raises(ds.SpecError) as exc:
        ds.load_brand_profile(tmp_path / "nope.json")
    assert "brand-specific" in str(exc.value)


def test_brand_profile_requires_its_sections(tmp_path):
    p = tmp_path / "partial.json"
    p.write_text(json.dumps({"colors": {}}), encoding="utf-8")
    with pytest.raises(ds.SpecError) as exc:
        ds.load_brand_profile(p)
    assert "photography" in str(exc.value)


def test_repository_brand_profile_is_valid_and_drives_a_spec():
    profile_path = Path(__file__).parents[4] / "_templates" / "social-creatives" / "brand-profile.json"
    profile = ds.load_brand_profile(profile_path)
    spec = ds.build_spec(brand_profile=profile)
    assert ds.layout_report(spec)["errors"] == 0
    # Nothing brand-specific may be hardcoded in the skill itself.
    assert spec["colors"]["primary"] == profile["colors"]["primary"]


def test_every_creative_type_and_candidate_combination_validates_clean():
    """The structural guarantee: no preset/candidate pairing may ship a layout
    that the validator itself rejects. The 'commercial' direction originally
    failed this — a vertically centred hook cannot coexist with a dominant
    subject, because the product is wider than the space left over."""
    profile = ds.load_brand_profile(
        Path(__file__).parents[4] / "_templates" / "social-creatives" / "brand-profile.json")
    for ctype in ds.CREATIVE_TYPES:
        for cand in ds.DEFAULT_CANDIDATES:
            spec = ds.build_spec(creative_type=ctype, candidate=cand, brand_profile=profile)
            report = ds.layout_report(spec)
            assert report["errors"] == 0, (
                f"{ctype}/{cand}: "
                + "; ".join(i["message"] for i in report["issues"] if i["severity"] == "error")
            )
