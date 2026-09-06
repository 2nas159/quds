# Render pack — سفرة رمضان carousel + 4:5 ad

Copy source: `social/2026-09-06-ramadan-iftar-bundle-sofret-ramadan-carousel-and-ad.md`
Skill: `.claude/skills/social-creative-designer` (SKILL.md Steps 5–8)

## STATUS (updated 2026-09-06, render session 2)

**DONE — rendered and QA-passed:**
- `slide-1-hook.png` — cover
- `ad-4x5-hook-a-convenience.png` — paid ad variant A
- `ad-4x5-hook-b-nostalgia.png` — paid ad variant B

  All three use `backgrounds/bg-hook-and-ad.jpg` (Gamma, 4:5, 1856×2304 — the full-spread
  flat-lay that Section A specifies for both the cover and the ad). RTL Arabic + phone
  number render correctly; torn banner, logo badge, starburst, green CTA pill all present.
  Note: one forearm in the photo has a small visible tattoo — acceptable (no face), swap the
  background if Enes objects.

**NOT DONE — blocked on image generation:**
- `slide-2-tier-small.png` … `slide-7-cta.png` (6 interior carousel slides).
  Every connected image service was out of credits after the one background above
  (Higgsfield 0 / no unlim; Gamma 10 credits left, all further requests 402'd).
  Each still needs its own background per Section A, then its Section B command.

**Slide 3 / Slide 4 — apply on render (per campaign non-negotiable, "توصيل مجاني" is BLOCKED
until Enes confirms each priced tier clears the 5,000 TRY free-delivery threshold):**
- Slide 3 `--subtext` → `"الأكثر طلبًا"` (drop `· توصيل مجاني`)
- Slide 4 `--subtext` → `"تكفي عزومة أو غدا العيد"` (drop `· توصيل مجاني`)

To finish slides 2–7: get an image tool with credit, generate the 6 backgrounds from
Section A into `backgrounds/`, then run their Section B commands (set
`PYTHONUTF8=1 PYTHONIOENCODING=utf-8` first on Windows, and use absolute paths).

---

Two mechanical steps per remaining output:

1. **Generate one background photo per output** from the prompts in Section A
   (aspect ratio 4:5, ~1600×2000; photography only — NO text, NO logos, NO badges, NO faces).
   Save them into `backgrounds/` in this folder with the filenames given.
2. **Run the `compose_slide.py` commands in Section B** (from the skill directory) to draw brand text.

Brand values already baked into the commands (from `_context/brand-style-guide.md` /
`_templates/social-creatives/STYLE-GUIDE.md`):
banner/badge/check `#b90f2a` · headline/footer/badge-text `#ffffff` · CTA pill `#25d366` ·
footer bg `#1a1a1a` · bullets `#1a1a1a` · logo `_templates/black logo.png` on default white badge.

---

## Section A — background image prompts (photography only, 4:5)

Shared style suffix for every prompt:
> Authentic working-butchery documentary photo. Bright, cool, fluorescent daylight interior. Stainless steel trays and counters. Shot from directly overhead or a slight angle, phone-camera realism, minor imperfection welcome, not glossy or over-polished. No text, no lettering, no logos, no watermarks, no signage, no faces, no people beyond gloved hands and forearms.

**bg-1-hook.jpg**
Overhead flat-lay of an abundant assortment of fresh raw lamb and beef cuts arranged in clusters across a large stainless steel tray on a stainless counter: a whole bone-in leg, a rack of ribs, cubed stewing meat, a big mound of ground meat, pale soup bones — grouped like a family spread. Generous empty negative space across the entire top third of the frame, some clear space along the bottom. Deep natural red meat tones.

**bg-2-tier-small.jpg**
A modest white cardboard butcher box on a stainless steel counter, partly filled with a small assortment of fresh raw meat: some cubed meat, a portion of ground meat, two pale soup bones. One hand in a black nitrile glove, forearm only, resting a wrapped portion into the box. Clear empty space across the top third for a text banner.

**bg-3-tier-mid-hero.jpg**
A generously filled white cardboard butcher box on a stainless steel counter, packed with a full assortment of fresh raw meat: bone-in leg and shoulder pieces, a section of ribs, cubed meat, a large mound of ground meat, soup bones. Two hands in black nitrile gloves, forearms only, arranging the cuts neatly. Feels abundant and organised. Clear empty space across the top third. Rich red meat tones.

**bg-4-tier-large.jpg**
Two large white cardboard butcher boxes and a big stainless tray side by side on a stainless steel counter, overflowing with a large assortment of fresh raw meat for a big gathering: whole leg and shoulder, multiple racks of ribs, piles of cubed meat, rolls of kofta-shaped ground meat, many soup bones. Hands in black nitrile gloves, forearms only, packing. Clear empty space across the top third.

**bg-5-trust.jpg**
Close-up of two hands in black nitrile gloves, forearms only, portioning fresh raw red meat on a clean stainless steel counter with a knife and cutting board. Spotless hygienic environment, stainless surfaces gleaming. Slight overhead angle. Clear empty space across the top third for a text banner.

**bg-6-how-it-works.jpg**
Hands in black nitrile gloves, forearms only, sealing a closed white cardboard delivery box with tape on a stainless steel counter, a roll of butcher's paper and a marker beside it, box ready to go out for delivery. Clean bright environment. Clear empty space across the top third.

**bg-7-cta.jpg**
A single closed white cardboard delivery box, taped and ready, on a clean stainless steel counter, a smartphone lying next to it showing a blank green messaging screen with no readable text. Slight overhead angle. Lots of clear empty space in the upper third and centre for text and a button.

**bg-ad-4x5.jpg**  (used for BOTH ad variants A and B)
Overhead flat-lay of a full "sofra" spread of fresh raw lamb and beef cuts on a large stainless steel tray and stainless counter: whole bone-in leg, a rack of ribs, cubed stewing meat, a big mound of ground meat, kofta rolls, pale soup bones, arranged in generous clusters. One hand in a black nitrile glove, forearm only, entering from one edge. Abundant, appetising, organised. Very generous empty negative space across the top third for a large headline banner; clear space in the lower third for a button and a badge in the bottom-left corner. Deep natural red meat tones.

---

## Section B — compose_slide.py commands

Run from `.claude/skills/social-creative-designer/`. Paths below are relative to the workspace root; adjust if running elsewhere. `pip install -r requirements.txt` first if deps are missing.
(PowerShell: replace the trailing `\` line-continuations with backticks, or put each command on one line.)

```bash
OUT=../../social/creatives/2026-09-06-sofret-ramadan
BG=../../social/creatives/2026-09-06-sofret-ramadan/backgrounds
LOGO="../../_templates/black logo.png"

# --- Slide 1 — hook / cover ---
python scripts/compose_slide.py \
  --background $BG/bg-1-hook.jpg --output $OUT/slide-1-hook.png \
  --headline "سفرة رمضان كلها بطلب واحد" --subtext "اختار حجم عيلتك واحنا نجهّزلك الباقي" \
  --headline-color "#ffffff" --banner-color "#b90f2a" --torn-banner \
  --logo "$LOGO" \
  --footer "توصيل سريع لباب بيتك · الدفع عند الاستلام · طازج لباب بيتك" \
  --footer-color "#ffffff" --footer-bg "#1a1a1a"

# --- Slide 2 — tier صغيرة ---
python scripts/compose_slide.py \
  --background $BG/bg-2-tier-small.jpg --output $OUT/slide-2-tier-small.png \
  --headline "صغيرة — لعيلة من ٣ لـ ٤ أفراد" --subtext "تكفي فطور عيلة صغيرة طول الأسبوع" \
  --headline-color "#ffffff" --banner-color "#b90f2a" --torn-banner \
  --logo "$LOGO" \
  --bullets "لحمة قطع للطواجن" "مفروم للمحاشي وورق العنب" "عظم ورقبة لشوربة رمضان" \
  --bullets-color "#1a1a1a" --check-color "#b90f2a" \
  --footer "اطلب على الواتساب: +90 534 570 30 37" --footer-color "#ffffff" --footer-bg "#1a1a1a"

# --- Slide 3 — tier وسط (HERO) ---
# NOTE: "توصيل مجاني" in subtext is BLOCKED pending Enes (tier must clear 5,000 TRY).
# If unconfirmed, change --subtext to: "الأكثر طلبًا"
python scripts/compose_slide.py \
  --background $BG/bg-3-tier-mid-hero.jpg --output $OUT/slide-3-tier-mid-hero.png \
  --headline "وسط — لعيلة من ٥ لـ ٦ أفراد" --subtext "الأكثر طلبًا · توصيل مجاني" \
  --headline-color "#ffffff" --banner-color "#b90f2a" --torn-banner \
  --logo "$LOGO" \
  --bullets "فخذ وكتف للطواجن والأوزي" "ريش ولحمة قطع للمشاوي" "مفروم للمحاشي وورق العنب" "عظم ورقبة للشوربة" \
  --bullets-color "#1a1a1a" --check-color "#b90f2a" \
  --badge-text "اختيار العيلة" --badge-color "#b90f2a" --badge-text-color "#ffffff" \
  --footer "اطلب على الواتساب: +90 534 570 30 37" --footer-color "#ffffff" --footer-bg "#1a1a1a"

# --- Slide 4 — tier كبيرة ---
# Same "توصيل مجاني" flag as Slide 3. If unconfirmed: --subtext "تكفي عزومة أو غدا العيد"
python scripts/compose_slide.py \
  --background $BG/bg-4-tier-large.jpg --output $OUT/slide-4-tier-large.png \
  --headline "كبيرة — للعزومة من ٨ لـ ١٠ أفراد" --subtext "تكفي عزومة أو غدا العيد · توصيل مجاني" \
  --headline-color "#ffffff" --banner-color "#b90f2a" --torn-banner \
  --logo "$LOGO" \
  --bullets "فخذ وكتف كاملة للأوزي والفرن" "ريش ولحمة قطع وكفتة للمشاوي" "مفروم كتير للمحاشي" "عظم ورقبة للشوربة" \
  --bullets-color "#1a1a1a" --check-color "#b90f2a" \
  --footer "اطلب على الواتساب: +90 534 570 30 37" --footer-color "#ffffff" --footer-bg "#1a1a1a"

# --- Slide 5 — trust ---
python scripts/compose_slide.py \
  --background $BG/bg-5-trust.jpg --output $OUT/slide-5-trust.png \
  --headline "ليه تطمن لسفرة القدس؟" \
  --headline-color "#ffffff" --banner-color "#b90f2a" --torn-banner \
  --logo "$LOGO" \
  --bullets "بنذبح ونقطّع بنفسنا في مكان نظيف وخاضع للرقابة" "كل صنف بيتقطّع طازة وقت الطلب — مش متخزّن" "الدفع كله عند الاستلام" \
  --bullets-color "#1a1a1a" --check-color "#b90f2a" \
  --footer "توصيل سريع لباب بيتك · الدفع عند الاستلام · طازج لباب بيتك" --footer-color "#ffffff" --footer-bg "#1a1a1a"

# --- Slide 6 — how it works ---
python scripts/compose_slide.py \
  --background $BG/bg-6-how-it-works.jpg --output $OUT/slide-6-how-it-works.png \
  --headline "طلبها في ٣ خطوات" \
  --headline-color "#ffffff" --banner-color "#b90f2a" --torn-banner \
  --logo "$LOGO" \
  --bullets "ابعتلنا رسالة واتساب واختار حجم عيلتك" "نجهّزها ونقطّعها طازة بإيدينا" "توصلك لباب البيت وتدفع وقت الاستلام" \
  --bullets-color "#1a1a1a" --check-color "#b90f2a" \
  --footer "توصيل سريع لباب بيتك · الدفع عند الاستلام · طازج لباب بيتك" --footer-color "#ffffff" --footer-bg "#1a1a1a"

# --- Slide 7 — CTA ---
python scripts/compose_slide.py \
  --background $BG/bg-7-cta.jpg --output $OUT/slide-7-cta.png \
  --headline "جهّز سفرة رمضان من غير زحمة" --subtext "رسالة واحدة على الواتساب واحنا نكمّل" \
  --headline-color "#ffffff" --banner-color "#b90f2a" --torn-banner \
  --logo "$LOGO" \
  --cta "اطلب الآن" --cta-color "#25d366" --cta-text-color "#ffffff" \
  --footer "+90 534 570 30 37 · باشاك شهير · اسنيورت · أرناؤوط كوي · بهتشه شهير" \
  --footer-color "#ffffff" --footer-bg "#1a1a1a"

# --- Ad 4:5 — Variant A (convenience / time) ---
python scripts/compose_slide.py \
  --background $BG/bg-ad-4x5.jpg --output $OUT/ad-4x5-hook-a-convenience.png \
  --headline "سفرة رمضان جاهزة من غير زحمة" \
  --headline-color "#ffffff" --banner-color "#b90f2a" --torn-banner \
  --logo "$LOGO" \
  --badge-text "قبل زحمة رمضان" --badge-color "#b90f2a" --badge-text-color "#ffffff" \
  --cta "اطلب الآن" --cta-color "#25d366" --cta-text-color "#ffffff" \
  --footer "توصيل سريع · الدفع عند الاستلام · +90 534 570 30 37" \
  --footer-color "#ffffff" --footer-bg "#1a1a1a"

# --- Ad 4:5 — Variant B (family / nostalgia) — SAME everything, hook only changes ---
python scripts/compose_slide.py \
  --background $BG/bg-ad-4x5.jpg --output $OUT/ad-4x5-hook-b-nostalgia.png \
  --headline "رمضان زمان على سفرتك" \
  --headline-color "#ffffff" --banner-color "#b90f2a" --torn-banner \
  --logo "$LOGO" \
  --badge-text "قبل زحمة رمضان" --badge-color "#b90f2a" --badge-text-color "#ffffff" \
  --cta "اطلب الآن" --cta-color "#25d366" --cta-text-color "#ffffff" \
  --footer "توصيل سريع · الدفع عند الاستلام · +90 534 570 30 37" \
  --footer-color "#ffffff" --footer-bg "#1a1a1a"
```

---

## Section C — after rendering

- Open every PNG and run the pre-publish checklist in
  `social/2026-09-06-ramadan-iftar-bundle-sofret-ramadan-carousel-and-ad.md`.
- If any headline wraps to 3+ lines or collides with the logo badge, shorten it (e.g.
  drop the "—" and use a space) rather than shrinking to an unreadable size.
- Carousel goes out as an ORGANIC Page post first; the ad is then built with
  "Use Existing Post" (campaign-strategist owns that step).
- The two `ad-4x5-hook-*` files are the A/B pair — launch each as a separate
  single-image ad inside the SAME ad set, 5–7 days minimum, compare Breakdown → By Ad.
