---
name: social-creative-designer
description: Designs and generates carousel-style social media graphics or single social visuals as PNG images — AI-generated photography composited with brand text (headline, CTA, footer) that is rendered separately for guaranteed-correct text, including right-to-left scripts like Arabic. Use this whenever the user asks for carousel slides, a swipe post, an Instagram/LinkedIn/Facebook carousel, a single social graphic or static post image, or wants a topic/piece of content turned into visual slides — even if they don't say "carousel" explicitly, e.g. "make some slides about X," "turn this into a post," "design a graphic for Y," or "I need visuals for the new promo." Make sure to trigger this skill any time the deliverable is a rendered image file rather than text copy.
---

# Social Creative Designer

Turns approved copy into art-directed social visuals. The workflow is
**content → design spec → image → composite → visual review → (bounded) revision**.
All brand specifics come from the workspace's `_context/` and `_templates/` at
runtime, so the skill stays reusable across brands.

## Why this shape

Two failure modes drive the design:

1. **Image models cannot render Arabic (or any RTL/complex script) reliably.** So
   the image model produces *photography only*, and `scripts/compose_slide.py`
   draws the text with real HarfBuzz shaping.
2. **An image model cannot be art-directed in prose.** "Leave negative space in
   the upper third" and a hand-typed `--label-y 0.40` are two people guessing
   independently — which is how labels ended up on top of products while the
   reserved empty space went unused. So layout is decided *once*, in a Design
   Spec, and both the image prompt and the compositor are derived from it.

The image model owns photography, subject, camera, lighting, realism, and
composing around reserved regions. It never owns typography, logo, CTA, badge,
placement, or brand colour.

## The pipeline

```
brief + approved copy
  → Design Spec  (scripts/design_spec.py)     ← art direction, as data
  → image prompt (scripts/image_prompt.py)    ← derived, never hand-written
  → photography  (whatever image tool is connected)
  → composite    (scripts/compose_slide.py --design-spec)
  → review       (scripts/review.py)          ← measures the actual PNG
  → PASS, or one routed revision (max 2), or an honest below-threshold report
```

## Step 1 — Brief

Pin down: topic, mode (carousel / single), slide count (default 3), aspect
(default 4:5), platform (default Instagram), and **paid vs organic**. Ask only
if a genuine ambiguity would change the work; otherwise apply defaults.

The caller should supply: objective, paid/organic, audience, topic, approved
copy, product, desired CTA, format, slide role, and any explicit creative
direction. Missing creative direction is fine — that is what this skill decides.
Missing *copy* is not: get it from the workspace's content agent first.

## Step 2 — Load brand context

Read `_context/brand-voice-guide.md`, `_context/brand-content.md`,
`_context/brand-style-guide.md`, and `_templates/social-creatives/STYLE-GUIDE.md`
(the measured visual spec — it is authoritative for layout). Add
`_context/product-offerings.md` if a product or price is named. Check the
project's `CLAUDE.md` for hard content rules; they override everything here.

The machine-readable half of the style guide is
`_templates/social-creatives/brand-profile.json` — palette, fonts, logo assets,
photography direction, and layout calibration measured off the reference
creatives. Every script takes it via `--brand-profile`. **Never hardcode a brand
value into this skill; add it to that file.**

## Step 3 — Design Spec

Build one spec per frame. `design_spec.py` composes it from a creative-type
preset → candidate art direction → brand calibration → your overrides.

- **Creative types**: `hero_offer`, `documentary_trust`, `value_list`, `cta_close`
- **Candidates**: `product_hero` (A), `documentary` (B), `commercial` (C)

For an important creative — a paid ad, a carousel cover — build **all three
candidates** and choose deliberately. They differ in subject scale, camera,
crop and where the negative space opens, not in adjectives. Do not default to A.

Validate before spending an image call:

```bash
python scripts/design_spec.py path/to/spec.json
```

It resolves every element to a box, auto-resolves collisions by hierarchy
(`subject > headline > cta > badge > logo > footer` unless the creative type says
otherwise), and reports safe-area, proportion and hierarchy errors. **Fix errors
here** — a layout error caught now costs nothing; caught after generation it
costs an image call.

## Step 4 — Image prompt

Derive it. Do not write one by hand:

```bash
python scripts/image_prompt.py spec.json --brand-profile <profile> [--json]
```

The reserved "keep this region visually quiet" clauses are computed from the
resolved layout boxes, so the photograph is composed around the exact areas the
compositor will draw into. Move the headline in the spec and the prompt follows.

Generate with whatever image tool is connected this session (varies —
check available MCP tools). Request the spec's exact dimensions. **If no image
tool is available or every call fails, say so plainly** — never present a
placeholder or a text description as the deliverable.

For carousel consistency, reuse one scene/style across frames or pass an earlier
frame as a reference image if the tool supports it.

## Step 5 — Composite

```bash
python scripts/compose_slide.py \
  --design-spec spec.json --brand-profile <profile> \
  --background bg.png --output slide-1.png --manifest slide-1.manifest.json
```

The spec supplies copy, placement and palette; any explicit flag still overrides
it, and the original CLI works unchanged (`--help` lists everything). The
compositor measures each element's real geometry *after* text shaping, resolves
collisions, then draws — so "does the badge sit on the CTA" is answered against
what is actually rendered.

**Always pass `--manifest`.** It records the boxes actually drawn; without it the
review step's geometry, contrast and thumbnail checks are inert.

On Windows set `PYTHONUTF8=1 PYTHONIOENCODING=utf-8` and use absolute paths.
Dependencies: `pip install -r requirements.txt`.

## Step 6 — Visual review

```bash
python scripts/review.py slide-1.png --manifest slide-1.manifest.json \
  --background bg.png --spec spec.json --thumbnail slide-1.thumb.png [--findings f.json]
```

Automated measurement catches what is measurable: padding/letterbox bands
anywhere in the frame, graphics crowding out the photograph, invisible
composited elements, collisions against real geometry, thumbnail legibility,
and subject prominence.

**You must also look at the image yourself** and at the thumbnail — glove
colour, fake-looking product, restaurant-vs-working lighting, anatomy, brand
feel and scroll-stopping power are not measurable. Pass your findings in via
`--findings` as:

```json
[{"category": "photography", "severity": "high",
  "issue": "lighting reads as warm restaurant photography, not working butchery",
  "correction": "use cooler fluorescent lighting and a stainless working surface"}]
```

Categories route the fix: `photography`/`lighting`/`realism`/`subject_framing` →
regenerate the image; `composition`/`hierarchy`/`product_prominence` → revise the
spec and recomposite; `collision`/`typography`/`rendering`/`proportion`/
`brand_consistency`/`legibility` → recomposite only. Never write "looks good" —
every finding needs a concrete correction.

`brand_consistency` is the ambiguous one: a wrong brand red is a compositor fix,
but wrong-coloured gloves can only be fixed by regenerating. When the defect is
**in the photograph**, add `"stage": "regenerate_image"` to the finding — without
it the correction routes to the compositor and never reaches the regeneration
that needed it.

Scoring is out of 100 (composition 25, product prominence 20, brand consistency
20, typography/layout 15, photography realism 10, CTA hierarchy 5, scroll-stopping
5). ≥85 ships; 75–84 revises; <75 regenerates; and any single high-severity
defect blocks the ship regardless of the total.

## Step 7 — Revision (bounded)

Apply the returned `corrections` at the stage `next_action` names — that is the
whole point of routing: **do not regenerate the image for a layout problem.**
For a photography fix, build the revision prompt with
`image_prompt.py --revision "<correction>" ...` so the new attempt keeps what the
last one got right.

Maximum **2** revision cycles. If it still fails, keep the best candidate, say
explicitly that it did not reach the threshold and why, and hand it over for a
human call. Do not report a failing creative as finished.

## Step 8 — Save

```text
social/creatives/<date>-<topic-slug>/
  slide-1-hook.png          spec/slide-1.json       (keep the specs —
  slide-1.manifest.json     slide-1.review.json      they are the edit history)
```

Single-image mode: one file in the same pattern, no subfolder needed. Flag
anything needing human sign-off (an unconfirmed price, a claim, a style call
you are unsure of) rather than presenting it as final.

## Reusing this skill for another brand

Replace `_templates/social-creatives/brand-profile.json`, the font files under
`assets/fonts/`, the logo assets it points at, and the reference creatives. The
scripts contain no brand names, colours, phone numbers, products or account IDs.
