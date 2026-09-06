# ملحمة القدس — Style Guide

This is the master reference for anyone (or any agent) producing content for ملحمة القدس. Read this first. Detailed context lives in the linked files.

---

## 1. Brand Snapshot

- **Business:** Dark Store / Cloud Butchery — no physical storefront. Orders via WhatsApp, fulfilled fresh, delivered cash-on-delivery.
- **Delivery zones:** Başakşehir, Esenyurt, Arnavutköy, Bahçeşehir (Istanbul, European side)
- **Audience:** Arabic-speaking community in Istanbul
- **WhatsApp:** +90 534 570 30 37
- **Owner:** Enes (male — use masculine Arabic verb forms when writing as/about him)

---

## 2. Voice — How We Talk

Warm, familiar, trustworthy. Like a neighbor you already trust — not a corporate brand.

- Egyptian-Arabic leaning colloquial, broadly understandable across dialects
- Short, conversational sentences — never long formal paragraphs
- Confident, never defensive — especially when addressing pricing or trust questions
- Emojis in moderation (🥩 🔥 📲 ✅) — enough for warmth, not so much it looks unprofessional
- Turkish used for Turkish-speaking customers (comments, bilingual materials)

**Never:**
- Formal/classical Arabic (فصحى) that feels stiff or distant
- Aggressive sales language
- Feminine verb forms referring to Enes
- Wall-of-text paragraphs

Full detail: `brand-voice-guide.md`

---

## 3. Visual Identity

### Colors

| Color | Hex | Usage |
|---|---|---|
| Primary Red | `#b90f2a` | Headline text on white paper banners, starburst badge, center banner panel, price accents |
| White | `#ffffff` | Torn paper banners, text on red, price pills, line icons |
| Near-Black | `#1a1a1a` | Old/strikethrough price pills, angled header banners, body text on light |
| WhatsApp Green | `#25d366` | The "اطلب الآن" CTA pill button **only** — never used decoratively |
| Sky Blue gradient | `#0b8ff5` → `#bfe4fb` | Background of multi-product catalog flyers only (see Format B) |

The blue gradient is a real, established part of the catalog-flyer look. It is the one sanctioned exception to the red/white/black core palette — do not extend it to hero posts.

### Typography

- Headlines/hooks/prices: **Cairo Bold** — set heavy and tight. On a hero post the hook sits **inside a compact torn-paper label**, not spanning the frame; size it to the label, not the canvas.
- Body/secondary text: **Cairo Regular** or **Tajawal**
- Arabic always right-to-left, never left-aligned

### Reference calibration (measured off `social/_references/`)

The three layout references (`1.png`, `2.png`, `3.png`) set the target proportions; `background.png` is a **photography-mood** reference only, no layout. Figures are % of canvas (height unless noted). `compose_slide.py` defaults are tuned to these:

| Element | Target | `compose_slide.py` token |
|---|---|---|
| Hook / product-name label | white **torn paper** patch, **red** Cairo Bold text; glyph height **5–6% H**; patch **7–12% H**, **25–55% W** (hugs the text), tilted ~−3°, soft drop shadow; sits **beside the product**, not across the top | `--banner-width hug` (default), `--banner-color #ffffff`, `--headline-color #b90f2a`, `--headline-scale 0.052`, `--label-x/--label-y/--label-tilt` |
| Curved pointer arrow | short white hand-drawn-style arc from the label to the cut it names | `--pointer X0 Y0 X1 Y1` |
| Logo | ~**13% W**, in a corner (refs use **top-right** and **bottom-right**), **no backing disc**, faint shadow only | `--logo`, `--logo-position tr` (default), `--logo-badge-color none` (default), `--logo-scale 0.13` |
| Contact line | small white text **on the photo, bottom-left, no bar**; ~**1.9% H**/line, drop-shadowed | `--footer`, `--footer-bg none` (default), `--footer-align left` (default), `--footer-scale 0.019` |
| Red starburst badge | ~**20–22% W** diameter, bottom-left | `--badge-text`, `--badge-scale 0.11` |
| Green WhatsApp CTA pill | ~**40–45% W × 6% H**, bottom-centre — **kept prominent** even though the refs de-emphasise their CTA (our funnel needs it obvious) | `--cta` |
| Photo coverage | **~100% full-bleed** — no top strip, no footer bar eating the frame | (removing the bars is the default now) |
| Outer margin | ~**4.5% W** | `--margin-scale 0.045` |

**Deliberate deviation from the references:** their CTA is a barely-visible phone number. Ours stays a full green pill — the CTA is the one element we do **not** shrink toward the references.

### Signature design elements

These recur across nearly every creative and are what make a post recognisably ملحمة القدس. Reproduce them, don't reinvent them:

- **Torn white paper label** — a small ripped-edge white paper patch carrying bold **red** Arabic text, tilted slightly, with a soft shadow. This is the single most identifiable brand device. It holds the hook (≤ ~4 words reads best) or a product name, and sits **beside the product it's about** — *not* as a full-width strip across the top edge. (A full-width strip is still available via `--banner-width full` for legacy layouts, but it is no longer the default look.)
- **Curved white arrow** — a short hand-drawn-feel arc from the torn label to the specific cut or detail it names. Pair it with the label whenever the label names one product.
- **Red starburst badge** — jagged spiky red disc, bold white Arabic inside (e.g. `اسعار منافسة`), bottom-left, ~20% of width.
- **Green WhatsApp CTA pill** — rounded green pill, bold white `اطلب الآن`, white circular WhatsApp glyph on the right end. Bottom-centre. Stays prominent.
- **White line-art trust icons** — outline hand-holding-banknotes and hand-holding-box icons with small bold white `الدفع عند الاستلام`, bottom-right.
- **Contact line on the photo** — WhatsApp number in small white text bottom-left, drawn straight on the photo with a drop shadow, **no black bar behind it**.
- **Price pills (catalog flyers)** — black pill with the struck-through old price sitting behind/above a white pill with the new price in heavy black. Sometimes a red `-XX%` flag.

### Photography direction

The brand's photography is **authentic working-butchery documentary**, not styled restaurant food photography. Get this wrong and the creative stops looking like the brand.

- Bright, cool, fluorescent/daylight interior lighting — **not** warm moody restaurant or dark grill-at-night lighting.
- Real environment: stainless steel trays and counters, product filling the frame edge to edge.
- **Black nitrile gloves** on the hands handling product — this is a deliberate hygiene/trust cue and appears constantly. Hands and forearms only.
- Shot from directly overhead or a slight angle, phone-camera realism, minor imperfection welcome. Over-polished glossy renders read as fake and undercut the trust angle.
- Never a face — Enes's or anyone's.
- Props (rosemary, citrus, peppers) used sparingly as freshness cues.

### Layout by format

**Format A — Hero/offer post (single product or single message).** The default for feed posts, ads, and carousel slides.

| Element | Position |
|---|---|
| Torn paper label, bold red Arabic hook/name | Beside the product — upper-left by default, tilted ~−3°, hugs the text (7–12% H). **Not** a full-width top strip. |
| Curved white arrow | From the label to the cut it names |
| Semi-transparent `ملحمة القدس` watermark | Centre, must not obscure product (optional — `--watermark`) |
| Small logo lockup | One corner, top-right default, ~13% W, no backing disc |
| Red starburst badge | Bottom-left, ~20% W |
| Green `اطلب الآن` WhatsApp pill | Bottom-centre, kept prominent |
| Contact line (WhatsApp number) | Bottom-left, small white text on the photo, no bar |
| White trust line-icons + `الدفع عند الاستلام` | Bottom-right (when used) |

Photo runs full-bleed behind all of it. See **Reference calibration** above for the measured ratios.

**Format B — Multi-product catalog flyer.** For price lists and range posts.

| Element | Position |
|---|---|
| Black angled/chevron header banner, white bold Arabic | Top |
| Red vertical centre column carrying the full logo lockup | Centre spine |
| Product cut-outs (isolated, no background) on blue gradient | 2–3 columns around the spine |
| Black old-price pill + white new-price pill per product | Under each product |
| Red star ribbon badge `جودة ونظافة عالية` | Top corner |
| Scooter line icon | Near the header |

### Logo

- Full lockup = sheep head outline + crossed cleavers + `ملحمة القدس` wordmark + `اجود انواع اللحوم` tagline.
- On **catalog flyers (Format B)** the lockup sits in the red centre spine.
- On **hero posts (Format A)** a **small** corner lockup (~13% W, no backing disc, top-right or bottom-right) is fine and matches the reference creatives — keep it unobtrusive so it doesn't compete with the photo. A centre watermark is an alternative, not a requirement. What to avoid is a large logo on a white circular badge dominating a corner.
- Use `white logo.png` on dark/busy areas, `black logo.png` on light areas.

### Production

- **Primary path — `compose_slide.py`** (in `.claude/skills/social-creative-designer/scripts/`): generate a text-free photographic background, then run the script to lay on the torn label, arrow, logo, starburst, CTA and contact line. It shapes Arabic correctly (HarfBuzz) and its defaults are calibrated to `social/_references/`. On Windows set `PYTHONUTF8=1 PYTHONIOENCODING=utf-8` and pass absolute paths. Key flags: `--headline` (hook, ≤ ~4 words reads best), `--banner-color/--headline-color` (default white paper / red text), `--label-x/--label-y/--label-tilt`, `--pointer X0 Y0 X1 Y1`, `--logo` + `--logo-position {tl,tr,bl,br}`, `--badge-text`, `--cta`, `--footer`. `--banner-width full` restores the legacy full-width top strip.
- **Canva** (Brand Kit `kAHKOEZjsF4`) is the fallback for work the script can't do — swap only hook text, product image, and price; keep layout identical across creatives so hook A/B tests stay clean. Note the Canva MCP connector mis-shapes Arabic and can't place the local logo — hand-build in the editor if using it.
- AI image tools cannot reproduce the logo lockup accurately. Generate the photographic base only; the script (or Canva) places the real logo asset.

Full detail: `brand-style-guide.md`

---

## 4. Content Rules — Hard Constraints

1. **NEVER mention or imply sourcing from a market** (e.g., Fatih market) in any public content, ad copy, or reply — no exceptions, no indirect hints.
2. **Never** reveal a physical store location — the business has none by design; frame this as intentional (lower costs → better prices for the customer).
3. **Always** use masculine Arabic verb forms when referring to Enes.
4. **Always** route pricing/order questions to WhatsApp — but give a real reason (weight-based pricing, daily updates), never make it feel like a secret.
5. **Never** use time-bound promotional wording (tied to a specific holiday/season) after that window has passed.

Full detail: `brand-content.md`

---

## 5. Core Messaging Pillars (use consistently)

- **توصيل سريع لباب بيتك** — Fast delivery to your door
- **الدفع عند الاستلام** — Cash on delivery
- **طازج لباب بيتك** — Fresh to your door

These should appear, in some form, across ad copy, captions, and comment replies — they directly address the Trust Gap (no physical store = need for transparency signals).

---

## 6. Standard CTA & Contact

- CTA button text: **اطلب الآن**
- WhatsApp: **+90 534 570 30 37**
- Free delivery threshold: orders over 5,000 TRY
- Delivery fee under 5,000 TRY: 150 TRY

---

## 7. Related Files

| File | Purpose |
|---|---|
| `brand-content.md` | Messaging pillars, hard content rules, Trust Gap context |
| `brand-voice-guide.md` | Full tone/language rules, sample phrases |
| `brand-style-guide.md` | Full visual identity spec |
| `growth-marketing-context.md` | Performance baselines, growth goals, ad objective learnings |
| `product-offerings.md` | Product catalog reference (live pricing endpoint pending) |
| `sop-meta-ads-campaign-management.md` | Campaign/ad set/creative launch process |
| `sop-content-production.md` | Creative production workflow, hook bank, caption structure |
| `sop-comment-and-dm-replies.md` | Approved reply scenarios |
| `sop-weekly-reporting.md` | Reporting cadence and decision triggers |
| `_templates/` | Fillable templates for briefs, captions, replies, reports, launch checklists |