---
name: social-creative-designer
description: Designs and generates carousel-style social media graphics or single social visuals as PNG images, using the Nano Banana MCP (mcp__nanobanana__generate_image) for image generation. Use this whenever the user asks for carousel slides, a swipe post, an Instagram/LinkedIn/Facebook carousel, a single social graphic or static post image, or wants a topic/piece of content turned into visual slides — even if they don't say "carousel" explicitly, e.g. "make some slides about X," "turn this into a post," "design a graphic for Y," or "I need visuals for the new promo." Make sure to trigger this skill any time the deliverable is a rendered image file rather than text copy.
---

# Social Creative Designer

Turns a topic or piece of content into a set of on-brand social media visuals — carousel slides or a single static graphic — rendered as PNG files via the Nano Banana MCP. This skill defines the *workflow*: it pulls all brand specifics (colors, fonts, voice, CTA, contact info, style direction) from the workspace's `_context/` and `_templates/` folders at runtime, so it stays reusable across brands as long as those folders exist.

## Why this shape

Image models are good at composition and mood but unreliable at rendering non-Latin script correctly, and they have no memory of "what this brand looks like" unless you tell them every time. So the workflow below front-loads brand grounding (read the guides, look at real reference creatives) before writing a single prompt, and it ends with a human-legibility check on any rendered text — skipping either step is what produces off-brand or garbled output.

## Step 1 — Clarify the brief

From the user's request, pin down:

- **Topic/content**: what the slides are about (a product, an offer, an educational point, a behind-the-scenes story, etc.)
- **Mode**: carousel (default) or single static image
- **Slide count**: default **3** for a carousel unless the user specifies otherwise
- **Aspect ratio**: default **4:5** (portrait). Also supports **1:1**, **3:4**, and landscape **1.91:1** if requested — see the Aspect Ratio Mapping table in Step 6, since Nano Banana's supported ratio list doesn't include 1.91:1 natively.
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

Write out the actual on-slide copy for each slide now, in the brand's voice and language rules from Step 2, before moving to image prompts — it's much easier to fix wording as text than to regenerate an image over a phrasing tweak.

## Step 5 — Build the image prompt for each slide

Each Nano Banana prompt should translate the brand spec into concrete visual instruction. Include:

- **Subject/scene**: what's actually depicted (product shot, hands-on process, lifestyle moment, abstract graphic panel — whatever fits the slide's content)
- **Composition & layout**: where text blocks, badges, logos, and CTA elements sit, based on the style direction chosen in Step 3
- **Exact on-slide copy**: quote the precise text from Step 4 that should render on the image, and specify its script/language explicitly (e.g. "Arabic text, right-to-left, reading: ...")
- **Color palette**: pull the hex values from the brand style guide rather than describing colors loosely ("the brand's primary red, #______")
- **Typography feel**: weight/style described in words (Nano Banana can't load a specific font file, so describe it — e.g. "bold, rounded sans-serif headline type")
- **Aspect ratio**: pass via the `aspect_ratio` parameter, not just described in the prompt (see Step 6)
- **What to avoid**: use `negative_prompt` for things the brand rules forbid appearing (e.g. faces, competing logos, text in the wrong language)

If the brand rules require specific fixed elements every creative needs (a phone number, a fixed CTA phrase, messaging pillars) work them into the copy naturally rather than listing them as a disconnected footer, unless the reference style shows them as a footer/badge convention.

For visual consistency across a carousel, generate slide 1 first, then pass it as `input_image_path_1` (alongside the new slide's prompt) when generating slides 2+, asking the model to keep the same visual system (palette, layout grid, typography style) while changing the content. This keeps a set feeling like one design instead of three unrelated images.

## Step 6 — Generate with Nano Banana

Call `mcp__nanobanana__generate_image` for each slide/frame with:

- `prompt`: the full prompt built in Step 5
- `aspect_ratio`: mapped from the requested ratio (table below)
- `negative_prompt`: as needed
- `input_image_path_1`: the prior slide, for carousel consistency (Step 5), or a chosen reference creative for style grounding on slide 1
- `output_path`: a real path in the workspace (Step 7), not the default temp location

**Aspect ratio mapping** (Nano Banana's supported set doesn't include every ratio this skill offers):

| Requested | Pass to `aspect_ratio` |
|---|---|
| 4:5 (default) | `4:5` |
| 1:1 | `1:1` |
| 3:4 | `3:4` |
| 1.91:1 (landscape) | `16:9` — closest supported ratio; note the substitution to the user since it isn't an exact match |

If the Nano Banana MCP (or any configured image generation tool) is unavailable or a call fails outright, **stop and tell the user explicitly** that MCP-generated images could not be produced — don't fall back to describing images in text or producing placeholder output as if it were a deliverable.

## Step 7 — Save and name outputs

Save generated PNGs under `social/creatives/<date>-<topic-slug>/`, following the workspace's kebab-case-with-date convention, e.g.:

```
social/creatives/2026-09-04-ramadan-promo/
  slide-1-hook.png
  slide-2-value.png
  slide-3-cta.png
```

For single-image mode, a single file in the same pattern (e.g. `social/creatives/2026-09-04-friday-special/post.png`) is enough — skip the subfolder if there's only one file, unless the user is building a set over time.

## Step 8 — Check before calling it done

Before presenting the output, verify:

- **Arabic (or other on-slide) text actually rendered correctly and legibly** — image models frequently garble non-Latin script. Look at the generated image directly; if the text is wrong, regenerate that slide rather than shipping it broken.
- **Text reads right-to-left** where the brand's language is RTL — check this visually, not just in the prompt.
- Nothing in the image violates a hard content rule from Step 2 (forbidden imagery, wrong language register, anything requiring sign-off like a live price)
- The visual set feels consistent (see Step 5) if it's a carousel
- Run any project-specific pre-publish checklist referenced in the workspace's SOPs, if one exists, before marking customer-facing content ready to publish

Flag anything that still needs human sign-off (an unconfirmed price, a style choice you're not fully sure about) rather than presenting it as finished.
