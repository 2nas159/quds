---
name: social-creative-designer
description: Designs and generates carousel-style social media graphics or single social visuals as PNG images — AI-generated photography composited with brand text (headline, CTA, footer) that is rendered separately for guaranteed-correct text, including right-to-left scripts like Arabic. Use this whenever the user asks for carousel slides, a swipe post, an Instagram/LinkedIn/Facebook carousel, a single social graphic or static post image, or wants a topic/piece of content turned into visual slides — even if they don't say "carousel" explicitly, e.g. "make some slides about X," "turn this into a post," "design a graphic for Y," or "I need visuals for the new promo." Make sure to trigger this skill any time the deliverable is a rendered image file rather than text copy.
---

# Social Creative Designer

Turns a topic or piece of content into a set of on-brand social media visuals — carousel slides or a single static graphic — rendered as PNG files. This skill defines the *workflow*: it pulls all brand specifics (colors, fonts, voice, CTA, contact info, style direction) from the workspace's `_context/` and `_templates/` folders at runtime, so it stays reusable across brands as long as those folders exist.

## Why this shape

Image models are good at composition and mood but unreliable at rendering non-Latin script correctly — this isn't specific to one provider, it's true of every mainstream image-generation model, because contextual letter-joining and right-to-left layout are underrepresented in training data compared to Latin text. Asking a model to bake Arabic (or any RTL/complex script) headline text directly into the image is a gamble that fails often enough to not be worth taking on a brand's actual content.

So this skill splits the work in two:

1. **AI image generation produces the photography only** — no text in the prompt at all. This is what image models are actually good at, and it's the one part of this workflow that needs whatever image-generation tool (MCP or otherwise) is currently available.
2. **The bundled `scripts/compose_slide.py` draws the brand's text on top** of that photography — headline banner, CTA pill, footer strip, logo — using real HarfBuzz text shaping (the same engine browsers use), not Pillow's default text drawing or an AI model's guess. This guarantees correct letter-joining and right-to-left order every time.

The workflow also front-loads brand grounding (read the guides, look at real reference creatives) before writing a single prompt — skipping that is what produces off-brand output even when the text is fine.

## Step 1 — Clarify the brief

From the user's request, pin down:

- **Topic/content**: what the slides are about (a product, an offer, an educational point, a behind-the-scenes story, etc.)
- **Mode**: carousel (default) or single static image
- **Slide count**: default **3** for a carousel unless the user specifies otherwise
- **Aspect ratio**: default **4:5** (portrait). Also supports **1:1**, **3:4**, and landscape **1.91:1** if requested.
- **Platform**: default **Instagram**. Also supports LinkedIn, Facebook, and others — platform mostly affects tone/format conventions (e.g. LinkedIn skews less emoji-heavy) more than the generation mechanics.

If any of these is genuinely ambiguous and would send the work in a materially different direction (e.g. is this a promo or an educational series?), ask. Otherwise apply the defaults and proceed — don't stall the whole workflow on minor preferences.

## Step 2 — Load brand context

Read these before writing any prompts (paths are relative to the workspace root; if a path doesn't exist, tell the user rather than inventing brand details):

1. `_context/brand-voice-guide.md` and `_context/brand-content.md` — tone, language, non-negotiable content rules
2. `_context/brand-style-guide.md` — full visual identity: colors, typography, logo/layout conventions
3. `_templates/social-creatives/STYLE-GUIDE.md` — the quick-reference visual spec and the index of reference creatives
4. If the topic names a product or price: `_context/product-offerings.md` (and flag any price as needing confirmation per the project's rules — never publish a specific price without sign-off)
5. If it's campaign/performance-related: `_context/growth-marketing-context.md`

Also check the project's root instructions (CLAUDE.md, if present) for hard content rules — things like what must never be shown or implied, whose face can't appear, which language forms are required. These override anything below.

## Step 3 — Pick a style direction

Unless the user has specified a style, open `_templates/social-creatives/STYLE-GUIDE.md` to see what visual directions exist, then look at the actual reference images it points to (use the Read tool on the image files — they're your directional inspiration, not a template to trace). Notice:

- Layout pattern (where hook text, logo, CTA, price/badges sit)
- Typography hierarchy (what's biggest/boldest, what's supporting text)
- Color usage and mood (how saturated, how much white space, photography style)

Pick the direction(s) that best fit the topic — a promo/discount topic might pull from a "discount flyer" style reference, an educational or trust-building topic might pull from a plainer product-forward style. **Adapt and recombine elements; don't replicate a reference exactly.** If the user names a specific style, use that one instead of choosing.

## Step 4 — Plan the slide sequence

For a carousel, structure content across slides like this:

- **Slide 1 — the hook.** Bold, attention-stopping headline. Minimal text — a single strong line or short phrase, not a paragraph. Its only job is to stop the scroll and earn the swipe.
- **Middle slides — value/education/insight.** Break the topic into digestible chunks, one idea per slide. This is where the substance lives.
- **Final slide — CTA or takeaway.** Either a clear call to action (drive to the brand's ordering channel) or a memorable summary of the key point, per what the topic calls for.

For single-image mode, compress this into one frame: apply the same "bold hook" direction from slide 1, adapted to carry a bit more supporting context since there's no follow-up slide.

**Write the on-slide copy through a copy specialist, not inline.** If the workspace defines a content/copywriting agent (check `.claude/agents/`), delegate the actual headline/subtext/bullet/CTA writing to it rather than drafting it yourself — that's what such an agent exists for, and copy written without that step tends to read as generic on-brand phrasing rather than something that actually earns a click. Tell it explicitly whether this is a **paid ad** or an organic post: paid delivery needs a real scroll-stopping hook and a genuine reason to act now (a rules-compliant urgency/scarcity angle — e.g. limited daily prep quantity, occasion framing — never a fake countdown or a price/discount not confirmed with the brand owner), not just tone-matched sentences. If no such agent exists in the workspace, write the copy yourself but hold it to that same bar before moving on: could a stranger scrolling past actually feel the hook, or does it just describe the product?

Decide which slides need which elements (a mid-value slide might skip the CTA pill; the final slide should have it prominently) once the copy is set.

## Step 5 — Generate the background photography

Write an image-generation prompt per slide/frame that describes **photography only — no text, no logos, no UI elements, no badges**. That all gets added in Step 6. Include:

- **Subject/scene**: what's actually depicted (product shot, hands-on process, lifestyle moment — whatever fits the slide's content)
- **Composition**: leave clear, uncluttered space where the headline banner, CTA pill, and footer will land (based on the style direction from Step 3) — e.g. "plenty of negative space in the upper third" if the headline banner goes there
- **Color mood**: nudge the palette toward the brand's colors where natural (warm reds, natural lighting) without expecting exact hex-accurate output from a photo generator
- **What to avoid**: faces (if the brand forbids showing a specific person), competing text, watermarks, logos

Use whatever image-generation tool is currently available (check connected MCP tools — Nano Banana, Higgsfield, Gamma's `generate_image`, or others vary by session). Request the aspect ratio the tool supports; if it doesn't expose the exact ratio requested in Step 1, note the substitution to the user rather than silently picking something else, and pick the closest available ratio (e.g. 4:5 or 1:1 over an unsupported 1.91:1).

**If no image-generation tool is available or every call fails, stop and tell the user explicitly** that AI-generated images could not be produced — don't fall back to describing images in text or producing placeholder output as if it were a deliverable.

For visual consistency across a carousel, either reuse one generated background/scene style across all slides (varying subject slightly) or pass an earlier slide as a reference/conditioning image if the tool supports it, so the set reads as one design system rather than unrelated photos.

## Step 6 — Composite the brand text

Run `scripts/compose_slide.py` on each background image to add the headline, CTA, footer, and logo. It shapes text with HarfBuzz and rasterizes with FreeType — this is what makes Arabic (or any RTL script) come out correctly instead of the tofu-boxes/garbled-order failure you get from Pillow's default text drawing or an image model's guess.

```bash
python scripts/compose_slide.py \
  --background path/to/generated-photo.png \
  --output social/creatives/<date>-<slug>/slide-1-hook.png \
  --headline "اللحمة علينا والشوي عليك" \
  --headline-color "#ffffff" \
  --banner-color "#b90f2a" \
  --cta "اطلب الآن" \
  --cta-color "#25D366" \
  --footer "توصيل سريع لباب بيتك · الدفع عند الاستلام" \
  --logo path/to/logo.png
```

Pull colors from the brand style guide (Step 2), not the defaults shown above — the defaults are just this brand's colors and won't be right for another. Run `python scripts/compose_slide.py --help` for the full option list; omit any flag for elements a given slide doesn't need (e.g. a mid-carousel value slide might skip `--cta`).

**A flat rectangle banner reads as a template, not a design.** Before settling for the plain form above, check whether the brand's reference creatives (Step 3) use devices like a torn-paper banner edge, a checkmark bullet list, or a starburst urgency/callout badge — this script supports all three, and using them is usually the difference between "on-brand" and actually looking designed:

- `--torn-banner` — jagged banner edge instead of a straight rectangle
- `--bullets "line one" "line two" "line three"` (with `--bullets-color` / `--check-color`) — a right-aligned checkmark list under the banner, for value/trust slides
- `--badge-text "..."` (with `--badge-color` / `--badge-text-color`) — a starburst badge, e.g. for a genuine urgency/scarcity line (never a fake countdown or an unconfirmed price)
- `--logo path/to/logo.png` (with `--logo-badge-color`) — places the logo top-left inside a backing-color circle so it reads on any photo; the script auto-detects and strips a flat-color logo background (common in exported logo files) rather than pasting a hard colored box. When a logo is present, the headline automatically reserves space for it and right-aligns instead of centering — don't fight this by re-centering manually, a centered long headline will run straight into the logo.

**Dependencies**: the script needs `Pillow`, `numpy`, `uharfbuzz`, and `freetype-py` (`pip install -r requirements.txt` from the skill directory if missing). It bundles Cairo and Tajawal (this brand's fonts, per the style guide) under `assets/fonts/` — swap in another brand's font files there if reusing this skill elsewhere, and update the `HEADLINE_FONT`/`BODY_FONT` paths at the top of the script accordingly. Each text field (headline/subtext/cta/footer/bullets) can freely mix Arabic and Latin/digits (e.g. a footer with a phone number) — the script splits mixed fields into bidi runs automatically, so a phone number's digit groups stay in order instead of scrambling. Characters the bundled fonts can't render (emoji, most notably — these text fonts carry no emoji glyphs) are silently dropped rather than drawn as tofu boxes; don't rely on emoji rendering in composited text.

## Step 7 — Save and name outputs

Save composited PNGs under `social/creatives/<date>-<topic-slug>/`, following the workspace's kebab-case-with-date convention, e.g.:

```text
social/creatives/2026-09-04-ramadan-promo/
  slide-1-hook.png
  slide-2-value.png
  slide-3-cta.png
```

For single-image mode, a single file in the same pattern (e.g. `social/creatives/2026-09-04-friday-special/post.png`) is enough — skip the subfolder if there's only one file, unless the user is building a set over time.

## Step 8 — Check before calling it done

Before presenting the output, look at each final composited image directly and verify:

- **Text is legible, correctly joined, and reads right-to-left** where the brand's language is RTL. The HarfBuzz pipeline in Step 6 should guarantee this, but confirm visually rather than assuming — a font missing a glyph or a mis-set flag can still produce a blank/wrong result.
- **The background photo has nothing that reads as text-shaped noise or a stray watermark** the image model might have added on its own
- Nothing in the image violates a hard content rule from Step 2 (forbidden imagery, wrong language register, anything requiring sign-off like a live price)
- The visual set feels consistent (Step 5) if it's a carousel
- Run any project-specific pre-publish checklist referenced in the workspace's SOPs, if one exists, before marking customer-facing content ready to publish

Flag anything that still needs human sign-off (an unconfirmed price, a style choice you're not fully sure about) rather than presenting it as finished.
