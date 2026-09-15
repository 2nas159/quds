"""Design Spec -> image prompt: derivation, determinism, brand-agnosticism."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import design_spec as ds  # noqa: E402
import image_prompt as ip  # noqa: E402

REPO = Path(__file__).parents[4]
PROFILE_PATH = REPO / "_templates" / "social-creatives" / "brand-profile.json"


@pytest.fixture
def profile():
    return ds.load_brand_profile(PROFILE_PATH)


@pytest.fixture
def spec(profile):
    return ds.build_spec(
        creative_type="hero_offer",
        candidate="product_hero",
        brand_profile=profile,
        overrides={
            "visual_objective": "make the cut immediately dominant",
            "subject": {"description": "a fresh bone-in lamb leg"},
            "elements": {"headline": {"text": "ريش خروف"}, "cta": {"text": "اطلب الآن"}},
        },
    )


def test_prompt_names_the_subject(spec, profile):
    assert "fresh bone-in lamb leg" in ip.build_image_prompt(spec, profile)


def test_prompt_states_a_subject_coverage_band(spec, profile):
    prompt = ip.build_image_prompt(spec, profile)
    assert "% of the" in prompt
    assert "dominant" in prompt


def test_prompt_carries_camera_and_crop_direction(spec, profile):
    prompt = ip.build_image_prompt(spec, profile)
    assert "Camera:" in prompt
    assert "directly overhead" in prompt  # product_hero candidate


def test_prompt_reserves_the_regions_the_layout_actually_uses(spec, profile):
    prompt = ip.build_image_prompt(spec, profile)
    assert "Reserved areas" in prompt
    assert "visually quiet" in prompt


def test_reserved_region_moves_when_the_headline_moves(profile):
    """The regression guard. Reserved negative space in the prompt is derived
    from the resolved layout — it cannot drift away from where the compositor
    will actually draw."""
    left = ds.build_spec(brand_profile=profile, overrides={"elements": {"headline": {"area": "upper_left"}}})
    right = ds.build_spec(brand_profile=profile, overrides={"elements": {"headline": {"area": "upper_right"}}})
    a, b = ip.build_image_prompt(left, profile), ip.build_image_prompt(right, profile)
    assert "upper-left region" in a
    assert "upper-right region" in b
    assert a != b


def test_prompt_forbids_text_and_logos(spec, profile):
    prompt = ip.build_image_prompt(spec, profile).lower()
    for banned in ("text", "logo", "watermark", "faces"):
        assert banned in prompt, f"{banned} must be excluded explicitly"


def test_prompt_demands_full_bleed(spec, profile):
    """The v2 background shipped with a blank white band because nothing asked
    for edge-to-edge photography."""
    prompt = ip.build_image_prompt(spec, profile)
    assert "edge-to-edge" in prompt
    assert "letterboxing" in prompt


def test_prompt_pulls_photography_direction_from_the_profile(spec, profile):
    prompt = ip.build_image_prompt(spec, profile)
    assert profile["photography"]["lighting"] in prompt
    assert profile["photography"]["environment"] in prompt


def test_prompt_is_brand_agnostic():
    """Swap the brand profile and nothing of the old brand survives — the skill
    itself holds no brand specifics."""
    other = {
        "colors": {"primary": "#0000ff"},
        "photography": {
            "genre": "clean studio still life",
            "lighting": "soft north-window light",
            "environment": "a pale oak tabletop",
            "avoid": ["clutter", "visible branding"],
        },
        "layout_calibration": {"margin": 0.05, "elements": {}},
    }
    spec = ds.build_spec(
        brand_profile=other,
        overrides={"subject": {"description": "a ceramic pour-over cone"}},
    )
    prompt = ip.build_image_prompt(spec, other).lower()
    assert "clean studio still life" in prompt
    assert "soft north-window light" in prompt
    for quds_ism in ("butchery", "nitrile", "meat", "stainless"):
        assert quds_ism not in prompt


def test_prompt_is_deterministic(spec, profile):
    assert ip.build_image_prompt(spec, profile) == ip.build_image_prompt(spec, profile)


def test_candidates_produce_materially_different_prompts(profile):
    prompts = {
        c: ip.build_image_prompt(ds.build_spec(candidate=c, brand_profile=profile), profile)
        for c in ds.DEFAULT_CANDIDATES
    }
    assert len(set(prompts.values())) == 3
    # Different in kind (scale/camera), not just in adjectives.
    assert "directly overhead" in prompts["product_hero"]
    assert "three-quarter" in prompts["commercial"]


def test_revision_prompt_appends_corrections(spec, profile):
    corrections = ["Increase subject scale by approximately 15-20%.", "Use cooler fluorescent lighting."]
    revised = ip.build_revision_prompt(spec, profile, corrections)
    assert ip.build_image_prompt(spec, profile) in revised
    assert "Corrections to apply" in revised
    for c in corrections:
        assert c in revised


def test_revision_prompt_without_corrections_is_the_base_prompt(spec, profile):
    assert ip.build_revision_prompt(spec, profile, []) == ip.build_image_prompt(spec, profile)


def test_prompt_bundle_carries_dimensions_and_negative_prompt(spec, profile):
    bundle = ip.prompt_bundle(spec, profile)
    assert bundle["width"] == 1080 and bundle["height"] == 1350
    assert bundle["negative_prompt"]
    assert bundle["candidate"] == "product_hero"


def test_trivial_regions_do_not_clutter_the_prompt(profile):
    """A 1%-of-canvas element is not worth a constraint clause."""
    spec = ds.build_spec(
        brand_profile=profile,
        overrides={"elements": {"footer": {"x": 0.05, "y": 0.93, "w": 0.05, "h": 0.01}}},
    )
    regions = ds.negative_space_regions(spec)
    footer = next(r for r in regions if r["for"] == "footer")
    assert ip._region_clause(footer, 0.8) is None


def test_cli_emits_a_prompt(tmp_path, spec, capsys):
    path = ds.save_spec(spec, tmp_path / "spec.json")
    assert ip.main([str(path), "--brand-profile", str(PROFILE_PATH)]) == 0
    assert "focal subject" in capsys.readouterr().out


def test_cli_reports_a_bad_spec(tmp_path, capsys):
    bad = tmp_path / "bad.json"
    bad.write_text('{"canvas": {"width": 1}}', encoding="utf-8")
    assert ip.main([str(bad), "--brand-profile", str(PROFILE_PATH)]) == 2
    assert "ERROR" in capsys.readouterr().out
