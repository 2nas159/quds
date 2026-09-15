"""Compositor: Design Spec integration, collision handling at render time,
manifest output, and backwards compatibility with the original CLI."""
import json
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

SCRIPTS = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import compose_slide as cs  # noqa: E402
import design_spec as ds  # noqa: E402

REPO = Path(__file__).parents[4]
PROFILE_PATH = REPO / "_templates" / "social-creatives" / "brand-profile.json"

HEADLINE = "ريش خروف"
CTA = "اطلب الآن"
FOOTER = "اطلب على الواتساب · +90 534 570 30 37"


@pytest.fixture
def background(tmp_path):
    rng = np.random.default_rng(11)
    arr = rng.integers(60, 190, size=(675, 540, 3), dtype=np.int16).astype(np.uint8)
    path = tmp_path / "bg.png"
    Image.fromarray(arr, "RGB").save(path)
    return path


def run(argv):
    return cs.main(argv)


# --------------------------------------------------------------------------
# Backwards compatibility — every pre-existing invocation must still work
# --------------------------------------------------------------------------


def test_legacy_minimal_invocation(background, tmp_path):
    out = tmp_path / "slide.png"
    assert run(["--background", str(background), "--output", str(out),
                "--headline", HEADLINE]) == 0
    assert Image.open(out).size == (540, 675)


def test_legacy_full_flag_set(background, tmp_path):
    """The exact shape of the commands already saved in this repo's render packs."""
    out = tmp_path / "slide.png"
    rc = run([
        "--background", str(background), "--output", str(out),
        "--headline", HEADLINE, "--subtext", "طازة كل يوم",
        "--headline-color", "#ffffff", "--banner-color", "#b90f2a", "--torn-banner",
        "--bullets", "توصيل سريع", "الدفع عند الاستلام", "طازج لباب بيتك",
        "--bullets-color", "#1a1a1a", "--check-color", "#b90f2a",
        "--badge-text", "اسعار منافسة", "--badge-color", "#b90f2a",
        "--cta", CTA, "--cta-color", "#25d366",
        "--footer", FOOTER, "--footer-color", "#ffffff", "--footer-bg", "#1a1a1a",
    ])
    assert rc in (0, 1)  # may report layout issues, must still render
    assert out.exists()


def test_legacy_full_width_banner_still_available(background, tmp_path):
    out = tmp_path / "slide.png"
    run(["--background", str(background), "--output", str(out),
         "--headline", HEADLINE, "--banner-width", "full", "--banner-position", "top",
         "--torn-banner"])
    top_strip = np.array(Image.open(out).convert("RGB"))[:20, :, :]
    assert top_strip.std() < 60, "the legacy full-width strip should dominate the top edge"


def test_legacy_output_is_byte_identical_without_a_design_spec(background, tmp_path):
    """Collision resolution defaults to 'warn' for bare CLI calls, so existing
    commands render exactly as they did before."""
    a, b = tmp_path / "a.png", tmp_path / "b.png"
    args = ["--background", str(background), "--headline", HEADLINE, "--cta", CTA,
            "--footer", FOOTER, "--badge-text", "جديد"]
    run(args + ["--output", str(a)])
    run(args + ["--output", str(b), "--collision-policy", "off"])
    assert a.read_bytes() == b.read_bytes()


def test_rendering_is_deterministic(background, tmp_path):
    a, b = tmp_path / "a.png", tmp_path / "b.png"
    args = ["--background", str(background), "--headline", HEADLINE, "--cta", CTA]
    run(args + ["--output", str(a)])
    run(args + ["--output", str(b)])
    assert a.read_bytes() == b.read_bytes()


@pytest.mark.parametrize("flags", [
    ["--logo-position", "tl"], ["--logo-position", "br"],
    ["--logo-badge-color", "#ffffff"], ["--watermark", None],
    ["--pointer", "0.3", "0.2", "0.52", "0.42"],
    ["--banner-color", "none"],
    ["--footer-align", "center"],
    ["--margin-scale", "0.08"],
])
def test_legacy_optional_flags_still_render(background, tmp_path, flags):
    logo = tmp_path / "logo.png"
    Image.new("RGBA", (120, 120), (255, 255, 255, 255)).save(logo)
    flags = [str(logo) if f is None else f for f in flags]
    out = tmp_path / "slide.png"
    run(["--background", str(background), "--output", str(out),
         "--headline", HEADLINE, "--logo", str(logo), "--footer", FOOTER] + flags)
    assert out.exists()


# --------------------------------------------------------------------------
# Design Spec integration
# --------------------------------------------------------------------------


def _spec(tmp_path, **overrides):
    profile = ds.load_brand_profile(PROFILE_PATH)
    spec = ds.build_spec(
        creative_type="hero_offer", candidate="product_hero", brand_profile=profile,
        canvas={"width": 540, "height": 675},
        overrides={
            "subject": {"description": "a rack of lamb ribs"},
            "elements": {
                "headline": {"text": HEADLINE},
                "cta": {"text": CTA},
                "footer": {"text": FOOTER},
            },
            **overrides,
        },
    )
    return ds.save_spec(spec, tmp_path / "spec.json")


def test_design_spec_supplies_copy_and_layout(background, tmp_path):
    spec = _spec(tmp_path)
    out = tmp_path / "slide.png"
    assert run(["--background", str(background), "--output", str(out),
                "--design-spec", str(spec)]) == 0
    assert out.exists()


def test_explicit_flag_overrides_the_spec(background, tmp_path):
    spec = _spec(tmp_path)
    out_spec, out_flag = tmp_path / "s.png", tmp_path / "f.png"
    run(["--background", str(background), "--output", str(out_spec), "--design-spec", str(spec)])
    run(["--background", str(background), "--output", str(out_flag), "--design-spec", str(spec),
         "--headline", "لحمة بلدي"])
    assert out_spec.read_bytes() != out_flag.read_bytes()


def test_disabled_element_is_not_drawn(background, tmp_path):
    with_cta = _spec(tmp_path)
    out_a = tmp_path / "a.png"
    run(["--background", str(background), "--output", str(out_a), "--design-spec", str(with_cta)])

    spec = json.loads(with_cta.read_text(encoding="utf-8"))
    spec["elements"]["cta"]["enabled"] = False
    no_cta = ds.save_spec(spec, tmp_path / "spec2.json")
    out_b = tmp_path / "b.png"
    run(["--background", str(background), "--output", str(out_b), "--design-spec", str(no_cta)])

    green = np.array([0x25, 0xD3, 0x66])
    def green_pixels(p):
        arr = np.array(Image.open(p).convert("RGB")).reshape(-1, 3)
        return int((np.abs(arr.astype(int) - green).sum(axis=1) < 40).sum())
    assert green_pixels(out_a) > 500
    assert green_pixels(out_b) == 0


def test_brand_profile_supplies_the_palette(background, tmp_path):
    """No brand colour is hardcoded in the compositor call."""
    out = tmp_path / "slide.png"
    run(["--background", str(background), "--output", str(out),
         "--design-spec", str(_spec(tmp_path)), "--brand-profile", str(PROFILE_PATH)])
    arr = np.array(Image.open(out).convert("RGB")).reshape(-1, 3)
    brand_red = np.array([0xB9, 0x0F, 0x2A])
    assert (np.abs(arr.astype(int) - brand_red).sum(axis=1) < 40).sum() > 200


def test_validate_only_renders_nothing(tmp_path):
    spec = _spec(tmp_path)
    out = tmp_path / "slide.png"
    assert run(["--design-spec", str(spec), "--validate-only"]) == 0
    assert not out.exists()


def test_validate_only_reports_a_bad_layout(tmp_path, capsys):
    spec = _spec(tmp_path, elements={"logo": {"width": 0.6}, "headline": {"text": HEADLINE}})
    assert run(["--design-spec", str(spec), "--validate-only"]) == 1
    assert "proportion" in capsys.readouterr().out


def test_validate_only_requires_a_spec(capsys):
    assert run(["--validate-only"]) == 2
    assert "needs a --design-spec" in capsys.readouterr().out


def test_background_and_output_are_required_without_validate_only():
    with pytest.raises(SystemExit):
        run(["--headline", HEADLINE])


# --------------------------------------------------------------------------
# Manifest — what was ACTUALLY drawn
# --------------------------------------------------------------------------


def test_manifest_records_real_measured_boxes(background, tmp_path):
    out, manifest = tmp_path / "slide.png", tmp_path / "m.json"
    run(["--background", str(background), "--output", str(out),
         "--design-spec", str(_spec(tmp_path)), "--manifest", str(manifest)])
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data["canvas"] == {"width": 540, "height": 675}
    for name in ("headline", "cta", "footer", "subject"):
        assert name in data["boxes"], f"{name} missing from manifest"
        assert len(data["boxes"][name]) == 4


def test_manifest_boxes_match_the_rendered_pixels(background, tmp_path):
    """The manifest is what the quality gate measures against — if it lies, the
    gate is measuring the wrong region."""
    out, manifest = tmp_path / "slide.png", tmp_path / "m.json"
    run(["--background", str(background), "--output", str(out),
         "--design-spec", str(_spec(tmp_path)), "--manifest", str(manifest)])
    data = json.loads(manifest.read_text(encoding="utf-8"))
    x, y, w, h = data["boxes"]["cta"]
    img = np.array(Image.open(out).convert("RGB"))
    ih, iw = img.shape[:2]
    patch = img[int(y * ih):int((y + h) * ih), int(x * iw):int((x + w) * iw)].reshape(-1, 3)
    green = np.array([0x25, 0xD3, 0x66])
    hits = (np.abs(patch.astype(int) - green).sum(axis=1) < 60).mean()
    assert hits > 0.4, f"CTA manifest box holds only {hits:.0%} pill pixels"


def test_manifest_records_collision_moves(background, tmp_path):
    spec = _spec(tmp_path, elements={
        "headline": {"text": HEADLINE},
        "badge": {"text": "جديد", "x": 0.30, "y": 0.84, "w": 0.22, "h": 0.16},
        "cta": {"text": CTA},
    })
    out, manifest = tmp_path / "slide.png", tmp_path / "m.json"
    run(["--background", str(background), "--output", str(out),
         "--design-spec", str(spec), "--manifest", str(manifest)])
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert "moves" in data and "issues" in data


# --------------------------------------------------------------------------
# Collision resolution at render time
# --------------------------------------------------------------------------


def test_colliding_badge_is_moved_off_the_cta(background, tmp_path):
    """Measured geometry, not the plan: the starburst and the pill are only
    known to collide after the text has been shaped."""
    spec = _spec(tmp_path, elements={
        "headline": {"text": HEADLINE},
        "cta": {"text": CTA},
        "badge": {"text": "جديد", "x": 0.40, "y": 0.83},
    })
    out, manifest = tmp_path / "slide.png", tmp_path / "m.json"
    run(["--background", str(background), "--output", str(out),
         "--design-spec", str(spec), "--manifest", str(manifest), "--collision-policy", "adjust"])
    boxes = json.loads(manifest.read_text(encoding="utf-8"))["boxes"]
    badge, cta = ds.Box(*boxes["badge"]), ds.Box(*boxes["cta"])
    assert max(badge.overlap_ratio(cta), cta.overlap_ratio(badge)) <= ds.OVERLAP_TOLERANCE


def test_collision_policy_off_leaves_positions_untouched(background, tmp_path):
    spec = _spec(tmp_path, elements={
        "headline": {"text": HEADLINE}, "cta": {"text": CTA},
        "badge": {"text": "جديد", "x": 0.40, "y": 0.83},
    })
    manifest = tmp_path / "m.json"
    run(["--background", str(background), "--output", str(tmp_path / "o.png"),
         "--design-spec", str(spec), "--manifest", str(manifest), "--collision-policy", "off"])
    assert json.loads(manifest.read_text(encoding="utf-8"))["moves"] == []


def test_adjusted_elements_stay_inside_the_safe_frame(background, tmp_path):
    spec = _spec(tmp_path, elements={
        "headline": {"text": HEADLINE}, "cta": {"text": CTA},
        "badge": {"text": "جديد", "x": 0.05, "y": 0.86},
        "footer": {"text": FOOTER},
    })
    manifest = tmp_path / "m.json"
    run(["--background", str(background), "--output", str(tmp_path / "o.png"),
         "--design-spec", str(spec), "--manifest", str(manifest)])
    boxes = json.loads(manifest.read_text(encoding="utf-8"))["boxes"]
    for name, values in boxes.items():
        if name in ("subject", "pointer"):
            continue
        box = ds.Box(*values)
        assert box.x >= -0.01 and box.y >= -0.01
        assert box.x1 <= 1.01 and box.y1 <= 1.01, f"{name} rendered outside the canvas"


def test_subtext_follows_the_headline_after_adjustment(background, tmp_path):
    spec = _spec(tmp_path, elements={
        "headline": {"text": HEADLINE, "y": 0.30},
        "subtext": {"text": "طازة كل يوم"},
    })
    manifest = tmp_path / "m.json"
    run(["--background", str(background), "--output", str(tmp_path / "o.png"),
         "--design-spec", str(spec), "--manifest", str(manifest)])
    boxes = json.loads(manifest.read_text(encoding="utf-8"))["boxes"]
    headline, subtext = ds.Box(*boxes["headline"]), ds.Box(*boxes["subtext"])
    assert subtext.y >= headline.y1 - 0.02, "subtext must sit under the label it belongs to"


# --------------------------------------------------------------------------
# Spec plumbing helpers
# --------------------------------------------------------------------------


def test_explicit_dests_detects_typed_flags():
    p = cs.argparse.ArgumentParser()
    p.add_argument("--headline")
    p.add_argument("--cta")
    found = cs._explicit_dests(p, ["--headline", "x"])
    assert found == {"headline"}


def test_explicit_dests_handles_equals_form():
    p = cs.argparse.ArgumentParser()
    p.add_argument("--headline")
    assert cs._explicit_dests(p, ["--headline=x"]) == {"headline"}


def test_dig_walks_a_dotted_path():
    assert cs._dig({"a": {"b": {"c": 3}}}, "a.b.c") == 3
    assert cs._dig({"a": {}}, "a.b.c") is None
    assert cs._dig({"a": 1}, "a.b") is None


def test_logo_area_is_translated_to_the_corner_vocabulary(tmp_path):
    class Args:
        logo_position = "tr"
    spec = {"elements": {"logo": {"area": "lower_left"}}}
    args = cs.apply_design_spec(Args(), spec, None, set())
    assert args.logo_position == "bl"


# --------------------------------------------------------------------------
# Text rendering (the part that must not regress)
# --------------------------------------------------------------------------


def test_arabic_shapes_without_tofu():
    shaped = cs.shape_line(HEADLINE, cs.HEADLINE_FONT, 48)
    assert shaped.width > 0 and shaped.height > 0


def test_mixed_arabic_and_latin_splits_into_bidi_runs():
    runs = cs.split_bidi_runs(FOOTER)
    assert any(cls == "EN" for cls, _ in runs)
    assert "+90 534 570 30 37" in "".join(t for c, t in runs if c == "EN")


def test_headline_max_width_shrinks_a_long_hook(background, tmp_path):
    long_hook = "سفرة رمضان كلها بطلب واحد من ملحمة القدس"
    narrow, wide = tmp_path / "n.json", tmp_path / "w.json"
    for path, mw in ((narrow, 0.35), (wide, 0.70)):
        spec = json.loads(_spec(tmp_path).read_text(encoding="utf-8"))
        spec["elements"]["headline"] = {"text": long_hook, "max_width": mw}
        ds.save_spec(spec, path)
    boxes = {}
    for key, path in (("n", narrow), ("w", wide)):
        manifest = tmp_path / f"{key}.m.json"
        run(["--background", str(background), "--output", str(tmp_path / f"{key}.png"),
             "--design-spec", str(path), "--manifest", str(manifest)])
        boxes[key] = ds.Box(*json.loads(manifest.read_text(encoding="utf-8"))["boxes"]["headline"])
    assert boxes["n"].w < boxes["w"].w


# --------------------------------------------------------------------------
# Brand-agnosticism of the compositor
# --------------------------------------------------------------------------


def test_brand_profile_swaps_the_font_faces(tmp_path, monkeypatch):
    """Another brand replaces its typefaces by editing its profile, not this
    script."""
    monkeypatch.setattr(cs, "HEADLINE_FONT", Path("sentinel"))
    cs.apply_brand_fonts({"fonts": {"headline": "assets/fonts/Tajawal-Bold.ttf"}})
    assert cs.HEADLINE_FONT.name == "Tajawal-Bold.ttf"
    assert cs.HEADLINE_FONT.exists()


def test_a_missing_brand_font_fails_loudly():
    with pytest.raises(SystemExit) as exc:
        cs.apply_brand_fonts({"fonts": {"headline": "assets/fonts/NoSuchFace.ttf"}})
    assert "not found" in str(exc.value)


def test_brand_fonts_resolve_beside_the_profile(tmp_path, monkeypatch):
    face = (SCRIPTS.parent / "assets" / "fonts" / "Cairo-Bold.ttf").read_bytes()
    (tmp_path / "faces").mkdir()
    (tmp_path / "faces" / "Custom.ttf").write_bytes(face)
    profile = tmp_path / "brand-profile.json"
    monkeypatch.setattr(cs, "BODY_FONT", Path("sentinel"))
    cs.apply_brand_fonts({"fonts": {"body": "faces/Custom.ttf"}}, profile)
    assert cs.BODY_FONT.name == "Custom.ttf"


def test_repository_brand_profile_fonts_all_resolve():
    cs.apply_brand_fonts(ds.load_brand_profile(PROFILE_PATH), PROFILE_PATH)
    for font in (cs.HEADLINE_FONT, cs.BODY_FONT, cs.BODY_FONT_BOLD):
        assert font.exists(), font
