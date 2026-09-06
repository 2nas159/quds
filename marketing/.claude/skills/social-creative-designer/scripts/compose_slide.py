#!/usr/bin/env python3
"""
Compose a social creative slide: takes a plain background photo (no baked-in
text — AI image models render Arabic unreliably) and draws brand text on top.

Why HarfBuzz instead of arabic_reshaper + Pillow's built-in text drawing:
Pillow on Windows ships without libraqm, so it can't shape Arabic itself.
The common workaround (arabic_reshaper + python-bidi, feeding Pillow plain
presentation-form characters) turned out to silently fail here: Cairo and
Tajawal don't include glyphs for several isolated/initial presentation-form
codepoints that arabic_reshaper emits, so those letters rendered as tofu
boxes. Shaping the text for real with HarfBuzz (same engine browsers use)
and rasterizing glyph-by-glyph with FreeType sidesteps that gap entirely —
it drives the font's actual OpenType joining rules instead of guessing at
precomposed codepoints.

Usage:
    python compose_slide.py --background bg.png --output slide-1.png \
        --headline "ريش خروف" \
        --pointer 0.30 0.20 0.52 0.42 \
        --cta "اطلب الآن" \
        --footer "اطلب على الواتساب · +90 534 570 30 37" \
        --logo path/to/white-logo.png --logo-position tr

The house default is the brand's compact torn WHITE paper label with RED
Cairo Bold text, sized to hug the hook and dropped beside the product with a
soft shadow and (optionally) a curved arrow — calibrated to the reference
creatives in social/_references/. The photo runs full-bleed: there is no
top strip and no footer bar by default. `--banner-width full` brings back
the old full-width top strip. `--help` lists every option; all colors are
hex; omit any element (label/cta/footer/logo/badge/pointer) a slide doesn't
need.

Each text field (headline/subtext/cta/footer) can freely mix Arabic and
Latin/digits (e.g. a footer with a phone number) — `split_bidi_runs` below
does a simplified version of the Unicode bidi algorithm to split the field
into same-direction runs before shaping, so a phone number's digits stay in
their own left-to-right order and reading order instead of getting
shattered at every space (what a naive single-direction shape does).
"""
import argparse
import math
import random
from pathlib import Path

import numpy as np
import uharfbuzz as hb
import freetype
from PIL import Image, ImageDraw, ImageFilter

FONT_DIR = Path(__file__).parent.parent / "assets" / "fonts"
HEADLINE_FONT = FONT_DIR / "Cairo-Bold.ttf"
BODY_FONT = FONT_DIR / "Tajawal-Regular.ttf"
BODY_FONT_BOLD = FONT_DIR / "Tajawal-Bold.ttf"


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def _glyph_to_array(bitmap):
    """FreeType pads each bitmap row to its `pitch`, which can exceed the
    glyph's actual width — reading the buffer as a flat width*height block
    (skipping this step) smears each row into the next and shreds the glyph."""
    w, h, pitch = bitmap.width, bitmap.rows, bitmap.pitch
    if w == 0 or h == 0:
        return None
    buf = np.array(bitmap.buffer, dtype=np.uint8)
    buf = buf.reshape(h, pitch)[:, :w] if pitch != w else buf.reshape(h, w)
    return buf


class ShapedText:
    """A HarfBuzz-shaped, FreeType-rasterized run of text as one RGBA image,
    plus the metrics needed to size/position it like a normal text block."""

    def __init__(self, text, font_path, px_size, direction="rtl", script="Arab", language="ar"):
        blob = hb.Blob.from_file_path(str(font_path))
        hb_face = hb.Face(blob)
        hb_font = hb.Font(hb_face)
        upem = hb_face.upem
        hb_font.scale = (upem, upem)

        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        buf.direction = direction
        buf.script = script
        buf.language = language
        hb.shape(hb_font, buf)

        ft_face = freetype.Face(str(font_path))
        ft_face.set_char_size(px_size * 64)
        scale = px_size / upem

        pen_x = pen_y = 0.0
        renders = []
        ascender = descender = 0
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            if info.codepoint == 0:
                # Glyph ID 0 is .notdef — HarfBuzz couldn't map this character
                # to anything in the font (this brand's fonts have no emoji
                # glyphs, for instance). Drop it silently rather than drawing
                # a tofu box or leaving a gap in the advance.
                continue
            ft_face.load_glyph(info.codepoint, freetype.FT_LOAD_RENDER)
            g = ft_face.glyph
            arr = _glyph_to_array(g.bitmap)
            x = pen_x + pos.x_offset * scale
            y = pen_y - pos.y_offset * scale
            if arr is not None:
                renders.append((arr, g.bitmap_left, g.bitmap_top, x, y))
                ascender = max(ascender, g.bitmap_top)
                descender = max(descender, g.bitmap.rows - g.bitmap_top)
            pen_x += pos.x_advance * scale
            pen_y += pos.y_advance * scale

        self.width = max(int(pen_x), 1)
        self.height = int(ascender + descender) or int(px_size * 1.2)
        self._renders = renders
        self._baseline = ascender

    def render(self, color):
        img = Image.new("RGBA", (self.width + 4, self.height + 4), (0, 0, 0, 0))
        for arr, left, top, x, y in self._renders:
            glyph_img = Image.fromarray(arr, mode="L")
            colored = Image.new("RGBA", glyph_img.size, tuple(color) + (0,))
            colored.putalpha(glyph_img)
            px = int(x) + left
            py = int(self._baseline - top + y)
            img.alpha_composite(colored, (px, py))
        return img


def split_bidi_runs(text):
    """Split text into direction-homogeneous runs, resolving neutrals (spaces,
    punctuation) to whichever side they sit between — same class on both
    sides keeps them attached to that run; a boundary between AR and EN
    defaults to AR, since that's this script's paragraph base direction.

    Without this, a phone number like "+90 534 570 30 37" embedded in an
    Arabic sentence gets torn apart at each internal space (each space read
    as a run boundary on its own), scrambling the digit-group order once the
    runs are reversed for RTL display. Resolving neutrals by their neighbors
    first keeps "+90 534 570 30 37" as one run, exactly like the real
    Unicode bidi algorithm's neutral-resolution rules (simplified to a single
    embedding level, which is all this skill's text fields need).
    """
    if not text:
        return []
    # First pass: classify true neutrals (whitespace/punctuation) separately
    # from EN/AR, then resolve them against their nearest strong neighbors.
    classes = []
    for ch in text:
        if ch.isascii() and (ch.isalnum() or ch == "+"):
            classes.append("EN")
        elif ch.isspace() or not ch.isalnum():
            classes.append("N")
        else:
            classes.append("AR")

    resolved = classes[:]
    i = 0
    while i < len(resolved):
        if resolved[i] == "N":
            j = i
            while j < len(resolved) and resolved[j] == "N":
                j += 1
            before = resolved[i - 1] if i > 0 else None
            after = resolved[j] if j < len(resolved) else None
            fill = before if before == after and before is not None else (before or after or "AR")
            for k in range(i, j):
                resolved[k] = fill
            i = j
        else:
            i += 1

    runs, current_class, current_text = [], resolved[0] if resolved else "AR", ""
    for ch, cls in zip(text, resolved):
        if cls != current_class and current_text:
            runs.append((current_class, current_text))
            current_text = ""
        current_class = cls
        current_text += ch
    if current_text:
        runs.append((current_class, current_text))
    return runs


class MultiRun:
    """A left-to-right sequence of ShapedText runs (already in draw order)
    treated as one block for sizing/positioning, e.g. via paste_centered."""

    def __init__(self, shaped_runs):
        self.runs = shaped_runs
        self.width = sum(r.width for r in shaped_runs)
        self.height = max((r.height for r in shaped_runs), default=0)

    def render(self, color):
        img = Image.new("RGBA", (max(self.width, 1) + 4, self.height + 4), (0, 0, 0, 0))
        x = 0
        baseline = max((r._baseline for r in self.runs), default=0)
        for r in self.runs:
            piece = r.render(color)
            img.alpha_composite(piece, (int(x), int(baseline - r._baseline)))
            x += r.width
        return img


def shape_line(text, font_path, px_size, direction="rtl"):
    """Shape a field that may mix Arabic and Latin/digits, splitting into
    bidi runs first (see split_bidi_runs) so mixed content like a phone
    number embedded in Arabic renders in the correct order and direction."""
    bidi_runs = split_bidi_runs(text)
    if len(bidi_runs) <= 1:
        return ShapedText(text, font_path, px_size, direction=direction)

    # Base direction RTL: visual left-to-right order is the reverse of
    # logical run order, with each run's own internal characters unchanged.
    ordered = list(reversed(bidi_runs)) if direction == "rtl" else bidi_runs
    shaped_runs = []
    for cls, run_text in ordered:
        if cls == "EN":
            shaped_runs.append(ShapedText(run_text, font_path, px_size, direction="ltr", script="Latin", language="en"))
        else:
            shaped_runs.append(ShapedText(run_text, font_path, px_size, direction="rtl", script="Arab", language="ar"))
    return MultiRun(shaped_runs)


def _greedy_wrap(words, font_path, size, max_width):
    lines, current = [], []
    for word in words:
        trial = " ".join(current + [word])
        if shape_line(trial, font_path, size).width <= max_width or not current:
            current.append(word)
        else:
            lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


def fit_and_wrap(text, font_path, max_width, max_height, start_size=90, min_size=28, balance=False):
    """Pick the largest font size (shrinking in steps) at which the text —
    wrapped word-by-word to max_width — fits within max_height.

    With balance=True, a multi-line result whose final line is a lone stub
    (one short word — the classic torn-label 'واحد' / 'زحمة' orphan) is
    re-wrapped to a tighter width so an earlier break pulls a second word
    down onto the last line. Only used for the headline label, where an
    orphan looks visibly wrong; bullets and badge text pass balance=False."""
    words = text.split(" ")
    size = start_size
    shaped_lines, line_height = None, size * 1.35
    while size >= min_size:
        lines = _greedy_wrap(words, font_path, size, max_width)
        if balance and len(lines) >= 2 and len(lines[-1].split(" ")) == 1:
            widest = max(shape_line(ln, font_path, size).width for ln in lines)
            for shrink in (0.92, 0.85, 0.78):
                trial = _greedy_wrap(words, font_path, size, widest * shrink)
                if len(trial) == len(lines) and len(trial[-1].split(" ")) >= 2:
                    lines = trial
                    break

        shaped_lines = [shape_line(line, font_path, size) for line in lines]
        line_height = size * 1.35
        total_height = line_height * len(shaped_lines)
        widest = max(s.width for s in shaped_lines)
        if total_height <= max_height and widest <= max_width:
            return shaped_lines, line_height
        size -= 4
    return shaped_lines, line_height


def chroma_key_flat_background(img, tolerance=18):
    """Logo exports often come as a flat-color square (solid white or solid
    black background) rather than true transparency. Sample the four
    corners; if they agree on one color, key that color out to alpha 0 so
    the logo sits on a photo as a mark instead of a hard colored box."""
    rgba = img.convert("RGBA")
    w, h = rgba.size
    corners = [rgba.getpixel((0, 0)), rgba.getpixel((w - 1, 0)), rgba.getpixel((0, h - 1)), rgba.getpixel((w - 1, h - 1))]
    r0, g0, b0 = corners[0][:3]
    if not all(abs(c[0] - r0) < tolerance and abs(c[1] - g0) < tolerance and abs(c[2] - b0) < tolerance for c in corners):
        return rgba
    arr = np.array(rgba)
    dist = np.abs(arr[..., 0].astype(int) - r0) + np.abs(arr[..., 1].astype(int) - g0) + np.abs(arr[..., 2].astype(int) - b0)
    mask = dist < tolerance * 3
    arr[..., 3] = np.where(mask, 0, arr[..., 3])
    return Image.fromarray(arr, mode="RGBA")


def draw_pill(draw, box, fill):
    radius = (box[3] - box[1]) // 2
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def paste_centered(canvas, shaped, color, center_x, top_y):
    glyph_img = shaped.render(color)
    x = int(center_x - glyph_img.width / 2)
    canvas.alpha_composite(glyph_img, (x, int(top_y)))


def paste_right_aligned(canvas, shaped, color, right_x, top_y):
    """Place a shaped block so its right edge lands at right_x — the natural
    anchor for RTL text blocks (bullets, right-aligned labels)."""
    glyph_img = shaped.render(color)
    x = int(right_x - glyph_img.width)
    canvas.alpha_composite(glyph_img, (x, int(top_y)))
    return glyph_img.width


def draw_torn_band(draw, w, band_top, band_bottom, fill, edge="bottom", jag=None, seed=7):
    """A flat rectangle reads as a generic banner. A torn-paper edge (small
    randomized zig-zag instead of a straight line) is what makes the brand's
    reference creatives (see _templates/social-creatives) feel like a made
    poster instead of a text box slapped on a photo — cheap to draw, does
    most of the work of making a slide look designed rather than templated.
    `edge` picks which side of the band gets torn: 'bottom' for a banner
    sitting at the top of the frame, 'top' for one sitting at the bottom.
    """
    rng = random.Random(seed)
    jag = jag or max(8, int(w * 0.012))
    step = max(18, int(w * 0.025))
    points_top = [(0, band_top), (w, band_top)]
    xs = list(range(0, w + step, step))
    torn = [(x, band_bottom + rng.randint(-jag, jag)) for x in xs]
    if edge == "bottom":
        polygon = [(0, band_top), (w, band_top), (w, band_bottom)] + list(reversed(torn)) + [(0, band_bottom)]
    else:
        torn_top = [(x, band_top + rng.randint(-jag, jag)) for x in xs]
        polygon = [(0, band_bottom), (w, band_bottom), (w, band_top)] + list(reversed(torn_top)) + [(0, band_top)]
    draw.polygon(polygon, fill=fill)


def draw_checkmark(draw, box, color, stroke=None):
    """A short check glyph (two strokes), not a font character — keeps
    bullet lists legible at small sizes without depending on a font glyph."""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    stroke = stroke or max(3, int(w * 0.14))
    p1 = (x0 + w * 0.05, y0 + h * 0.55)
    p2 = (x0 + w * 0.4, y0 + h * 0.85)
    p3 = (x0 + w * 0.95, y0 + h * 0.15)
    draw.line([p1, p2], fill=color, width=stroke, joint="curve")
    draw.line([p2, p3], fill=color, width=stroke, joint="curve")
    r = stroke // 2
    for p in (p1, p2, p3):
        draw.ellipse((p[0] - r, p[1] - r, p[0] + r, p[1] + r), fill=color)


def draw_bullets(canvas, draw, bullets, font_path, px_size, text_color, check_color, right_x, left_limit, top_y, line_gap=1.5):
    """Right-aligned checkmark bullet list (the brand's established value-list
    pattern) — checkmark sits at the RTL reading start (the right edge),
    text extends leftward from it, and long bullets wrap to the box width."""
    y = top_y
    check_size = int(px_size * 0.9)
    gap = int(px_size * 0.35)
    max_text_width = right_x - left_limit - check_size - gap
    for bullet in bullets:
        shaped = shape_line(bullet, font_path, px_size)
        if shaped.width > max_text_width:
            lines, line_h = fit_and_wrap(bullet, font_path, max_text_width, px_size * 3, start_size=px_size, min_size=max(18, px_size - 10))
        else:
            lines, line_h = [shaped], px_size * 1.35
        check_box = (right_x - check_size, int(y + (line_h - check_size) / 2), right_x, int(y + (line_h - check_size) / 2) + check_size)
        draw_checkmark(draw, check_box, check_color)
        for line in lines:
            paste_right_aligned(canvas, line, text_color, right_x - check_size - gap, y)
            y += line_h
        y += px_size * (line_gap - 1)
    return y


def draw_starburst(draw, center, outer_r, inner_r, points, fill):
    cx, cy = center
    poly = []
    for i in range(points * 2):
        angle = (i * math.pi / points) - math.pi / 2
        r = outer_r if i % 2 == 0 else inner_r
        poly.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    draw.polygon(poly, fill=fill)


def make_torn_patch(w, h, fill, seed=7, jag_frac=0.06):
    """The brand's product tag (STYLE-GUIDE ss3) is a *small* ripped label —
    a white paper rectangle torn along its long edges, cut clean at the ends —
    not the full-width strip the earlier layout drew. Build it at an arbitrary
    size on its own RGBA image so it can be tilted and shadowed as a unit.
    Returns (image, top_headroom): the image is `h` tall plus a little vertical
    slack top and bottom for the jagged edge, and top_headroom is where the
    paper's nominal top sits inside it."""
    rng = random.Random(seed)
    jag = max(4, int(h * jag_frac))
    hd = jag + 4
    img = Image.new("RGBA", (w, h + 2 * hd), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    step = max(12, int(w * 0.045))
    xs = list(range(0, w + step, step))
    top = [(min(x, w), hd + rng.randint(-jag, jag)) for x in xs]
    bot = [(min(x, w), hd + h + rng.randint(-jag, jag)) for x in xs]
    d.polygon(top + list(reversed(bot)), fill=fill)
    return img, hd


def soft_shadow(mask_img, blur, alpha=120):
    """A black, blurred copy of an RGBA image's own alpha — dropped behind
    text, labels and the logo so they stay legible sitting straight on a busy
    photo. The references do this instead of backing everything with a solid
    bar."""
    sh = Image.new("RGBA", mask_img.size, (0, 0, 0, 0))
    sh.paste((0, 0, 0, alpha), (0, 0), mask_img.split()[3])
    return sh.filter(ImageFilter.GaussianBlur(blur))


def paste_with_shadow(canvas, img, xy, blur=4, offset=(2, 3), alpha=120):
    canvas.alpha_composite(soft_shadow(img, blur, alpha),
                           (int(xy[0] + offset[0]), int(xy[1] + offset[1])))
    canvas.alpha_composite(img, (int(xy[0]), int(xy[1])))


def draw_curved_arrow(canvas, p0, p1, color, stroke, bow=0.28):
    """Short, hand-drawn-feel curved arrow from a product tag to the cut it
    names (STYLE-GUIDE ss3; references 1 and 2). A quadratic bezier with its
    control point pushed off the midpoint perpendicular to the chord, plus a
    two-stroke head at the tip. Drawn with a soft shadow so it reads on the
    photo."""
    (x0, y0), (x1, y1) = p0, p1
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1.0
    cx, cy = mx + (-dy / L) * L * bow, my + (dx / L) * L * bow
    pts = []
    for i in range(41):
        t = i / 40
        pts.append(((1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t ** 2 * x1,
                    (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t ** 2 * y1))
    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).line([(x + 2, y + 3) for x, y in pts],
                            fill=(0, 0, 0, 120), width=stroke, joint="curve")
    canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(3)))
    d = ImageDraw.Draw(canvas)
    d.line(pts, fill=tuple(color), width=stroke, joint="curve")
    ax, ay = pts[-1]
    bx, by = pts[-6]
    ang = math.atan2(ay - by, ax - bx)
    hl = stroke * 3.6
    for a in (ang + 2.5, ang - 2.5):
        d.line([(ax, ay), (ax - hl * math.cos(a), ay - hl * math.sin(a))],
               fill=tuple(color), width=stroke, joint="curve")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--background", required=True, help="Path to the AI-generated background photo (no text)")
    p.add_argument("--output", required=True, help="Path to write the final composed PNG")
    p.add_argument("--headline", help="Main hook / product-name text (Arabic)")
    # House default is the brand's torn WHITE paper label carrying RED text
    # (STYLE-GUIDE ss3), sized to hug the text — not a red bar with white text
    # spanning the whole top edge.
    p.add_argument("--headline-color", default="#b90f2a", help="Headline text color")
    p.add_argument("--banner-color", default="#ffffff", help="Label paper color, or 'none' for text straight on the photo")
    p.add_argument("--banner-width", choices=["hug", "full"], default="hug",
                   help="hug = compact torn label wrapped to the text (default, matches the reference creatives); full = legacy full-width strip")
    p.add_argument("--banner-position", choices=["top", "center", "bottom"], default="center",
                   help="Vertical zone for a --banner-width full strip. Ignored for hug (use --label-x/--label-y).")
    p.add_argument("--label-x", type=float, default=0.045, help="hug label: left inset as a fraction of width")
    p.add_argument("--label-y", type=float, default=0.40, help="hug label: nominal top as a fraction of height")
    p.add_argument("--label-tilt", type=float, default=-3.0, help="hug label: rotation in degrees (0 for none)")
    p.add_argument("--headline-scale", type=float, default=0.052, help="Headline start size as a fraction of canvas height")
    p.add_argument("--headline-min-scale", type=float, default=0.040, help="Smallest headline size as a fraction of canvas height")
    p.add_argument("--subtext", help="Optional smaller supporting line under the headline")
    p.add_argument("--cta", help="CTA pill text, e.g. اطلب الآن")
    p.add_argument("--cta-color", default="#25D366", help="CTA pill background color (brand WhatsApp green by default)")
    p.add_argument("--cta-text-color", default="#ffffff")
    p.add_argument("--footer", help="Small contact line, e.g. WhatsApp number + delivery areas")
    p.add_argument("--footer-color", default="#ffffff")
    p.add_argument("--footer-bg", default="none", help="Footer backing color, or 'none' (default) for text straight on the photo")
    p.add_argument("--footer-align", choices=["left", "center"], default="left")
    p.add_argument("--footer-scale", type=float, default=0.019, help="Footer text size as a fraction of canvas height")
    p.add_argument("--logo", help="Optional logo image")
    p.add_argument("--logo-position", choices=["tl", "tr", "bl", "br"], default="tr",
                   help="Which corner the logo sits in (references use top-right and bottom-right)")
    p.add_argument("--logo-badge-color", default="none", help="Backing disc behind the logo, or 'none' (default) to sit it straight on the photo")
    p.add_argument("--logo-scale", type=float, default=0.13, help="Logo width as a fraction of canvas width")
    p.add_argument("--torn-banner", action="store_true", help="(hug labels are always torn) force a torn edge on a --banner-width full strip")
    p.add_argument("--bullets", nargs="+", help="Checkmark bullet list drawn below the label (short phrases, not full sentences)")
    p.add_argument("--bullets-color", default="#ffffff", help="Bullet text color — white by default now that bullets sit on the photo, not a panel")
    p.add_argument("--check-color", default="#b90f2a")
    p.add_argument("--badge-text", help="Short text for a starburst badge (e.g. an urgency/scarcity line) — 1-3 short words, placed bottom-left")
    p.add_argument("--badge-color", default="#b90f2a")
    p.add_argument("--badge-text-color", default="#ffffff")
    p.add_argument("--badge-scale", type=float, default=0.11, help="Starburst radius as a fraction of canvas width")
    p.add_argument("--pointer", nargs=4, type=float, metavar=("X0", "Y0", "X1", "Y1"),
                   help="Draw a curved arrow between two fractional (0-1) points, label -> product detail")
    p.add_argument("--watermark", help="Optional logo image to drop in faint behind the text, centre of frame")
    p.add_argument("--margin-scale", type=float, default=0.045, help="Outer margin as a fraction of canvas width")
    args = p.parse_args()

    base = Image.open(args.background).convert("RGBA")
    w, h = base.size
    canvas = Image.new("RGBA", (w, h))
    canvas.alpha_composite(base)

    # Faint centre watermark sits behind everything else (STYLE-GUIDE Format A).
    if args.watermark:
        wm = Image.open(args.watermark).convert("RGBA")
        wm = chroma_key_flat_background(wm)
        tw = int(w * 0.5)
        wm.thumbnail((tw, tw))
        wm.putalpha(wm.split()[3].point(lambda v: int(v * 0.22)))
        canvas.alpha_composite(wm, ((w - wm.width) // 2, (h - wm.height) // 2))

    draw = ImageDraw.Draw(canvas)
    margin = int(w * args.margin_scale)
    hl_start = max(24, int(h * args.headline_scale))
    hl_min = max(18, int(h * args.headline_min_scale))
    red = hex_to_rgb(args.headline_color)
    label_bottom = int(h * 0.14)  # where bullets start if there is no headline

    if args.headline and args.banner_width == "full":
        # ---- legacy full-width strip (kept for callers that ask for it) ----
        banner_h = int(h * 0.20)
        if args.banner_position == "top":
            band = (0, 0, w, banner_h)
        elif args.banner_position == "bottom":
            band = (0, h - banner_h, w, h)
        else:
            band = (0, (h - banner_h) // 2, w, (h + banner_h) // 2)
        if args.banner_color.lower() != "none":
            if args.torn_banner:
                edge = "bottom" if args.banner_position == "top" else "top"
                draw_torn_band(draw, w, band[1], band[3], hex_to_rgb(args.banner_color), edge=edge)
            else:
                draw.rectangle(band, fill=hex_to_rgb(args.banner_color))
        lines, line_h = fit_and_wrap(args.headline, HEADLINE_FONT, w - 2 * margin,
                                     banner_h - 2 * margin, start_size=hl_start, min_size=hl_min)
        y = band[1] + (banner_h - line_h * len(lines)) / 2
        for shaped in lines:
            paste_centered(canvas, shaped, red, w / 2, y)
            y += line_h
        if args.subtext:
            sub = shape_line(args.subtext, BODY_FONT, max(24, int(banner_h * 0.12)))
            paste_centered(canvas, sub, red, w / 2, y + 6)
            y += sub.height
        label_bottom = band[3] if args.banner_position != "bottom" else band[1]

    elif args.headline:
        # ---- compact torn paper label (default) --------------------------
        # The reference tag carries a short product name (2-4 words). Keep it
        # roughly to the reference footprint (~7-12% of height): cap the text
        # box height so a longer hook shrinks its font instead of stacking
        # three full-size lines and ballooning the patch.
        pad_x, pad_y = int(w * 0.035), int(h * 0.014)
        max_text_w = int(w * 0.72) - 2 * pad_x
        lines, line_h = fit_and_wrap(args.headline, HEADLINE_FONT, max_text_w, h * 0.16,
                                     start_size=hl_start, min_size=hl_min, balance=True)
        text_w = max(s.width for s in lines)
        text_h = int(line_h * len(lines))
        lx, ly = int(w * args.label_x), int(h * args.label_y)

        if args.banner_color.lower() == "none":
            ty = ly
            for shaped in lines:
                g = shaped.render(red)
                paste_with_shadow(canvas, g, (lx, ty), blur=int(h * 0.005), offset=(3, 4), alpha=130)
                ty += line_h
            label_bottom = int(ty)
        else:
            patch_w, patch_h = text_w + 2 * pad_x, text_h + 2 * pad_y
            paper, hd = make_torn_patch(patch_w, patch_h, hex_to_rgb(args.banner_color) + (255,))
            for i, shaped in enumerate(lines):
                g = shaped.render(red)
                paper.alpha_composite(g, (int((patch_w - g.width) / 2), int(hd + pad_y + i * line_h)))
            if args.label_tilt:
                paper = paper.rotate(args.label_tilt, expand=True, resample=Image.BICUBIC)
            paste_with_shadow(canvas, paper, (lx, ly - hd), blur=int(h * 0.006), offset=(4, 7), alpha=110)
            label_bottom = ly - hd + paper.height

        if args.subtext:
            # The subtext sits on the photo just under the paper, not on it —
            # so it is white with a shadow, never the red used on the paper.
            sub = shape_line(args.subtext, BODY_FONT_BOLD, max(20, int(h * 0.024)))
            sub_img = sub.render((255, 255, 255))
            paste_with_shadow(canvas, sub_img, (lx + int(w * 0.008), label_bottom + int(h * 0.006)),
                              blur=4, offset=(2, 3), alpha=150)
            label_bottom = label_bottom + int(h * 0.006) + sub_img.height

    if args.bullets:
        # Render onto a transparent layer, shadow the whole layer, then
        # composite — so white bullet text holds up on a bright photo without
        # a backing panel.
        bullet_size = max(24, int(w * 0.030))
        layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        draw_bullets(layer, ImageDraw.Draw(layer), args.bullets, BODY_FONT_BOLD, bullet_size,
                     hex_to_rgb(args.bullets_color), hex_to_rgb(args.check_color),
                     right_x=w - margin, left_limit=margin,
                     top_y=int(label_bottom) + int(h * 0.03))
        canvas.alpha_composite(soft_shadow(layer, 5, 130))
        canvas.alpha_composite(layer)

    if args.pointer:
        x0, y0, x1, y1 = args.pointer
        draw_curved_arrow(canvas, (x0 * w, y0 * h), (x1 * w, y1 * h),
                          (255, 255, 255), max(4, int(w * 0.006)))

    if args.logo:
        logo = Image.open(args.logo).convert("RGBA")
        logo = chroma_key_flat_background(logo)
        logo_size = int(w * args.logo_scale)
        logo.thumbnail((logo_size, logo_size))
        lx = margin if args.logo_position in ("tl", "bl") else w - margin - logo.width
        ly = margin if args.logo_position in ("tl", "tr") else h - margin - logo.height
        if args.logo_badge_color.lower() != "none":
            badge_r = int(max(logo.width, logo.height) * 0.72)
            cx, cy = lx + logo.width // 2, ly + logo.height // 2
            badge = Image.new("RGBA", (badge_r * 2, badge_r * 2), (0, 0, 0, 0))
            ImageDraw.Draw(badge).ellipse((0, 0, badge_r * 2, badge_r * 2), fill=hex_to_rgb(args.logo_badge_color) + (255,))
            canvas.alpha_composite(badge, (cx - badge_r, cy - badge_r))
            canvas.alpha_composite(logo, (cx - logo.width // 2, cy - logo.height // 2))
        else:
            # A whisper of shadow so the mark reads whether it lands on a light
            # or dark patch of the photo.
            canvas.alpha_composite(soft_shadow(logo, 6, 85), (lx + 2, ly + 3))
            canvas.alpha_composite(logo, (lx, ly))

    if args.badge_text:
        badge_r = int(w * args.badge_scale)
        cx, cy = int(w * 0.16), int(h * 0.82)
        draw_starburst(ImageDraw.Draw(canvas), (cx, cy), badge_r, int(badge_r * 0.62), 10, hex_to_rgb(args.badge_color))
        blines, blh = fit_and_wrap(args.badge_text, BODY_FONT_BOLD, int(badge_r * 1.3), int(badge_r * 1.2),
                                   start_size=int(badge_r * 0.34), min_size=16)
        by = cy - blh * len(blines) / 2
        for line in blines:
            paste_centered(canvas, line, hex_to_rgb(args.badge_text_color), cx, by)
            by += blh

    foot_block_h = 0
    if args.footer:
        foot_size = max(16, int(h * args.footer_scale))
        foot = shape_line(args.footer, BODY_FONT, foot_size)
        foot_img = foot.render(hex_to_rgb(args.footer_color))
        foot_block_h = foot_img.height + margin
        if args.footer_bg.lower() != "none":
            strip_h = int(foot_img.height + 2 * int(h * 0.02))
            ImageDraw.Draw(canvas).rectangle((0, h - strip_h, w, h), fill=hex_to_rgb(args.footer_bg))
            canvas.alpha_composite(foot_img, (int((w - foot_img.width) / 2),
                                              int(h - strip_h + (strip_h - foot_img.height) / 2)))
        else:
            fx = margin if args.footer_align == "left" else (w - foot_img.width) / 2
            paste_with_shadow(canvas, foot_img, (fx, h - margin - foot_img.height),
                              blur=4, offset=(2, 3), alpha=150)

    if args.cta:
        cta_size = max(28, int(w * 0.045))
        cta_shaped = shape_line(args.cta, BODY_FONT_BOLD, cta_size)
        pad_x, pad_y = int(w * 0.06), int(h * 0.018)
        pill_w, pill_h = cta_shaped.width + 2 * pad_x, cta_shaped.height + 2 * pad_y
        pill_top = h - foot_block_h - pill_h - margin
        pill_box = ((w - pill_w) / 2, pill_top, (w - pill_w) / 2 + pill_w, pill_top + pill_h)
        draw_pill(ImageDraw.Draw(canvas), pill_box, hex_to_rgb(args.cta_color))
        paste_centered(canvas, cta_shaped, hex_to_rgb(args.cta_text_color), w / 2, pill_top + pad_y)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(args.output)
    print(f"Saved {args.output} ({w}x{h})")


if __name__ == "__main__":
    main()
