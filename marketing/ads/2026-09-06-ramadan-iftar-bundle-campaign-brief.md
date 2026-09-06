# Campaign Brief — Ramadan Iftar Meat Bundle ("سفرة رمضان")

**Date written:** 2026-09-06
**Author:** campaign-strategist
**Status:** PLANNING ONLY — no live Meta campaign created, updated, or touched. Nothing goes live until the "Needs Enes to confirm" list is cleared and downstream creative is produced and approved.
**Campaign window:** ~20 Jan 2027 – ~10 Mar 2027 (anchored to Ramadan 2027, ~7 Feb start / Eid al-Fitr ~8–9 Mar — reconfirm by moon sighting in January).
**Inputs used:**
- `research/2026-09-06-ramadan-iftar-bundle-market-research.md`
- `_context/growth-marketing-context.md`, `_context/product-offerings.md`, `_context/brand-content.md`, `_context/brand-voice-guide.md`
- `_sop/sop-meta-ads-campaign-management.md`
- **No `data-analyst` report exists in `reports/` yet.** Baselines below are taken from the documented figures in `growth-marketing-context.md`. Before launch (January), `data-analyst` should produce a current performance snapshot so the starting budget and cost-per-conversation target can be re-anchored to live numbers.

---

## 1. Strategic Rationale — what we promote and why

**Promote:** a named, fixed-contents Arabic "Iftar table" meat bundle — **"سفرة رمضان"** (working name; final naming is `content-creator`'s call) — in **three household-size tiers**, mid tier as the hero.

**Why now / why this:**
- Ramadan is the single highest-intent meat-buying occasion of the year for our Arabic-speaking audience (Syrian/Egyptian/Levantine hosting nights, عزومات, nostalgia-driven "Ramadan like back home").
- **Clear market gap in our four zones:** no Arabic-community butcher here publishes a clearly packaged, clearly sized, clearly priced iftar bundle. Competitors sell loose cuts or dry-goods boxes. This is an ownable position.
- Our structural advantage over Arabic-community competitors (who only claim "farm to table") is real behind-the-scenes trust content — in-house butchering, hygiene, cash on delivery. Ramadan creative that rewarded in the region in 2026 was warm, familiar, anti-glossy — which is exactly our lane.
- Prior ROAS on this account is ~14x with cost per conversation in a healthy 25–35 TRY band; the model is proven, this is a seasonal scale-up of it, not an experiment.

**Primary angle:** convenience for the occasion — *your iftar table, planned and delivered, without the pre-adhan queue.* Time and calm framing. One WhatsApp message.
**Supporting angles:** family / tradition / nostalgia; trust (in-house butchering, hygiene, COD).
**Hard constraint on the angle:** the convenience hook stays on *your evening, your kitchen, your queue* — **never** on where the meat comes from (Rule #1, no market-sourcing implication). "مش محتاج تقف في الزحمة قبل الأذان" is fine; anything about a market is not.

---

## 2. Objective & Campaign Structure

| Setting | Value | Source / reason |
|---|---|---|
| Objective | **OUTCOME_SALES**, optimized for Messaging (WhatsApp conversations) | SOP §1; documented account learning — Sales objective consistently beats Engagement here |
| Never use | OUTCOME_ENGAGEMENT | Tested, underperformed badly on cost-per-conversation and order conversion |
| Destination | **WhatsApp only** | SOP §1 — do not select "all messaging destinations"; splits budget, breaks order tracking |
| CTA | "Send WhatsApp Message" → **+90 534 570 30 37** | SOP §2 Step 4 |
| Campaign count | **One** campaign for the whole run | Objective cannot be changed mid-flight (SOP §9); all three phases live under this one campaign |
| Account | Ad Account `4318851221675090` · Business `1068514784536305` · Page `1190105444176095` | growth context |

**Carousel + Messaging-objective API workaround (SOP §2 / §8, growth context):**
Carousel creatives attached programmatically to a Messaging-objective ad hit Meta errors `#1487891` and `#1885090`. Required sequence for every carousel and every Messaging-objective creative:
1. `campaign-strategist` creates campaign (PAUSED) and ad set(s) (PAUSED) via API.
2. `content-creator` / `creative-designer` deliver the creative; it is **published organically as a Page post first**.
3. In Ads Manager UI, create the ad inside the existing ad set using **"Use Existing Post."**
4. Set CTA to "Send WhatsApp Message," turn the **ad** ON.
5. Do **not** pause the ad set or campaign at any point — only pause individual underperforming ads.

**Ad set structure:**

| Ad set | Audience | Budget behaviour | When it starts |
|---|---|---|---|
| **A — Core cluster** | Başakşehir (+2km), Esenyurt, Arnavutköy (+2km) · Arabic language · no interest layers | Scaled 10–20% increments (see §4) | Phase 1 launch |
| **B — Bahçeşehir (test)** | Bahçeşehir only · Arabic language · no interest layers | Flat test budget, read separately | Phase 1 launch — **optional, Enes to greenlight** |
| **C — Retargeting** | Custom Audience: people who messaged / engaged the Page or IG in last 365 days, minus known paying customers · all four zones | Small flat budget | Phase 1 launch — **contingent on the Custom Audience being built** |
| **D — Lookalike (optional)** | 1–3% Lookalike off the paying-customer list · all four zones · Arabic | Small flat budget | Phase 2 only, **only if** the seed customer list is large enough to build a LAL |

All four ad sets sit under the one OUTCOME_SALES / WhatsApp campaign. New creative always goes **into the existing ad set** — never a new ad set to "refresh."

---

## 3. Audience & Targeting

**Geography** (SOP §3): the four delivery zones — Başakşehir (+2km radius), Esenyurt, Arnavutköy (+2km radius), Bahçeşehir. Reference audience size for the 3–4 zone cluster is ~220k–260k.

**Language:** Arabic. **Detailed targeting / interests: none.** SOP §3 is explicit — location + language has proven sufficient; interest layers narrow reach and raise cost. Do not add "halal," "Ramadan," "Middle Eastern cuisine," etc.

**Split Bahçeşehir into its own ad set (Ad Set B):** **Yes — recommended**, per the medium-term growth goal to "expand coverage to Bahçeşehir as a distinct ad set, testing performance separately from the core Başakşehir/Esenyurt/Arnavutköy cluster." Keeping it separate means we get a clean read on whether Bahçeşehir converts at the same cost per conversation before folding it into the core cluster. If the envelope is tight, Enes can (a) hold Ad Set B to a smaller flat budget, or (b) delay it to Phase 2 — but do not merge it into Ad Set A for this campaign.

**Retargeting prior messagers (Ad Set C):** re-engage people who messaged but did not order — this is a standing short-term growth goal and Ramadan is the ideal moment to act on it. Requires a Custom Audience of Page/IG engagers + past WhatsApp click-throughs (last 365 days), with the paying-customer list excluded. `data-analyst` + Enes need to assemble the customer phone list so it can be uploaded as a Custom Audience and used as the exclusion. If the audience cannot be built in time, drop Ad Set C rather than delay the campaign.

**Custom Audience + Lookalike from paying customers:** building the paying-customer Custom Audience is a short-term growth goal in its own right. For this campaign it powers (a) the retargeting exclusion and (b) an optional 1–3% Lookalike ad set (D) in Phase 2. LAL only runs if the matched seed list is large enough for Meta to build one; otherwise skip it — no substitute seed.

**Delivery scheduling:** weight ad delivery to **sunset → late evening**; pull back during peak fasting daylight hours. MENA food-ad guidance is consistent that daytime fasting-hours food messaging underperforms and can irritate. Use ad-set dayparting from Phase 2 onward (through-Ramadan); Phase 1 (pre-Ramadan, people not yet fasting) can run standard delivery.

---

## 4. Budget & Phased Scaling

**Anchors:**
- SOP §4: start new campaigns/ad sets at **300 TRY/day**; scale in **10–20% increments only**; never scale by turning things off/on.
- Documented healthy **cost per messaging conversation: 25–35 TRY** (refresh/expand signal at 45–50+).
- Prior spend rate: 8,400 TRY over the 21 Jul – 4 Sep window (~46 days) ≈ ~180 TRY/day average; Eid al-Adha campaign ~175 TRY/day over 5 days. This campaign deliberately runs 2–4x that daily rate because Ramadan is the peak occasion and ROAS history (~14x) supports it — but every step stays inside the 10–20% rule so the learning phase is protected.

**Ad Set A — Core cluster (the headline budget):**

| Phase | Dates | Start → end daily budget | Scaling rule | Phase spend (est.) |
|---|---|---|---|---|
| 1 — Pre-Ramadan stock-up | 20 Jan – 6 Feb 2027 (~18 days) | 300 → ~480 TRY/day | +15% every 3–4 days **only if** cost/conv < 35 TRY and frequency < 3 | ~6,500–7,500 TRY |
| 2 — Through Ramadan | 7 Feb – 4 Mar 2027 (~26 days) | ~480 → ~830 TRY/day | +10–20% weekly, same guardrails; hold or step back if cost/conv drifts toward 45 | ~15,000–17,500 TRY |
| 3 — Last 10 days / pre-Eid | 28 Feb – 9 Mar 2027, budget peak 5–9 Mar (~5 peak days) | step up to ~900–950 TRY/day for the hosting peak, then ramp **down** post-Eid | ~4,500–5,500 TRY |
| **Ad Set A total** | | | | **~26,000–30,500 TRY** |

**Ad Set B — Bahçeşehir (optional):** flat **250 TRY/day** test budget for the full run (~49 days) ≈ **~12,000 TRY**. Do not scale it until it has its own clean cost-per-conversation read; if it holds under 35 TRY for 10+ days, Enes may fold it into the core scaling logic.

**Ad Set C — Retargeting (contingent):** flat **150 TRY/day** for the full run ≈ **~7,000 TRY**. Warm audience; expect lower cost per conversation. Do not scale aggressively — the audience is small and frequency will climb fast; refresh creative rather than raise budget.

**Ad Set D — Lookalike (optional, Phase 2 only):** flat **200 TRY/day** for ~30 days ≈ **~6,000 TRY**, only if built.

**Total campaign envelope:**

| Scope | Planned | Ceiling (do-not-exceed without new sign-off) |
|---|---|---|
| Core only (Ad Set A) | ~28,000 TRY | ~32,000 TRY |
| + Bahçeşehir + Retargeting | ~47,000 TRY | ~52,000 TRY |
| + Lookalike (all four ad sets) | ~53,000 TRY | ~58,000 TRY |

Enes signs off which scope to fund before anything is built. If only the core scope is approved, Ad Sets B/C/D are shelved, not delayed into a rushed mid-campaign launch.

**Mechanics reminder:** budget changes across phases are **edits to the existing ad set's daily budget**. Phases are creative/messaging shifts, not new campaigns or new ad sets. The campaign and all ad sets run continuously from Phase 1 launch until the post-Eid wind-down.

---

## 5. Timeline

All dates anchored to **Ramadan 2027 ≈ 7 Feb 2027 start, Eid al-Fitr ≈ 8–9 Mar 2027.** Reconfirm by moon sighting in January; shift the whole calendar with it.

| Milestone | Dates | Owner | What happens |
|---|---|---|---|
| **Build week** | 5–19 Jan 2027 | content-creator, creative-designer | Bundle name locked, all Phase 1 copy + Reels scripts + tier carousel + 4:5 static hooks produced and approved. `data-analyst` delivers a pre-launch performance snapshot. Custom Audience + (if viable) Lookalike built. |
| **Campaign build** | 15–19 Jan 2027 | campaign-strategist | Create campaign (PAUSED) + ad sets (PAUSED) via API. Publish Drop 1 creative as organic Page posts. Run the launch checklist (§9). |
| **Phase 1 — pre-Ramadan stock-up** | **20 Jan – 6 Feb 2027** | campaign-strategist | Ads ON. Angle: "order once, freezer-ready for the first week." Larger baskets. Standard delivery scheduling. |
| **Phase 2 — through Ramadan (weekly top-up)** | **7 Feb – 4 Mar 2027** | campaign-strategist | Angle: "this week's iftars sorted in one message." Dayparting to sunset–late evening. Creative refresh every 7–10 days into the same ad set. |
| **Phase 3 — last 10 days / pre-Eid عزومة push** | **28 Feb – 9 Mar 2027** (budget peak 5–9 Mar) | campaign-strategist | Re-emphasise the **large tier** for hosting nights and Eid lunch. "عزومة الليلة؟ رسالة واحدة ويوصلك بكرة." |
| **Wind-down** | **10–12 Mar 2027** | campaign-strategist | Ramp Ad Set A budget **down** over 2–3 days, then turn **ads** OFF. Leave campaign + ad set structure intact (never a hard pause mid-learning). Retire "سفرة رمضان" cleanly — no "sale ending" language, per growth-context guidance on season-tied wording. |

**Creative-refresh cadence** (research: same asset fatigues in 7–10 days; plan ~8–12 creatives across the run): fresh creative added to the **same ad set** every **7–10 days**. Never pause to reset. Pause only an individual ad, and only once a fresher ad in the set is beating it.

| Drop | ~Date | Adds to ad set |
|---|---|---|
| 1 | 20 Jan (launch) | Tier carousel (as existing-post ad) + Reel 1 "unboxing the bundle" + 4:5 static hook A |
| 2 | 28–30 Jan | Reel 2 "prep / in-house butchering" + 4:5 static hook B |
| 3 | 6–7 Feb (Ramadan start) | Reel 3 "countdown to iftar" + refreshed tier carousel |
| 4 | 14–15 Feb | Reel variant (weekly top-up framing) + 4:5 static hook C |
| 5 | 22–23 Feb | New Reel + "this week's table" static |
| 6 | 28 Feb – 1 Mar | Reel 5 "عزومة الليلة؟" large-tier + large-tier-forward carousel |
| 7 | 5–6 Mar | Final pre-Eid urgency creative (large tier, "يوصلك قبل العيد") |

Retargeting ad set (C) gets its own lighter refresh — one new creative roughly every 10–12 days, since the audience is small.

---

## 6. Bundle Structure (for creative + for Enes to finalise)

Three tiers by household size, using the ~250–400 g meat-per-person planning norm. **Exact cut mix and weights are Enes's to finalise against stock and daily cost** — the ranges below are the research planning anchor, not a spec.

| Tier | Arabic label (working) | Household | Approx. total weight | Role |
|---|---|---|---|---|
| Small | صغيرة — لعيلة صغيرة (٣–٤ أفراد) | 3–4 people | ~2.5–3.5 kg mixed | Entry / trial |
| **Mid** | **وسط — لعيلة (٥–٦ أفراد)** | **5–6 people** | **~4.5–6 kg mixed** | **HERO — default, most-promoted tier** |
| Large | كبيرة — للعزومة (٨–١٠ أفراد) | 8–10 people | ~8–10 kg mixed | Hosting nights + last 10 days + Eid |

**Contents principle:** map cuts to **familiar Ramadan dishes named in Arabic**, not Turkish cut names. Name the dish next to the cut. Coverage target across the bundle:
- طواجن / أوزي / لحمة بالفرن → فخذ / كتف / رقبة (leg / shoulder / neck pieces)
- مشاوي / عزومة → ريش / لحم قطع + كفتة / سجق
- محاشي / كوسا وورق عنب → مفروم (ground)
- شوربة رمضان → عظم للشوربة / رقبة (soup bones / neck)

**Optional suhoor mini add-on:** مفروم / كبدة / سجق — competitors ignore suhoor entirely. Include only if Enes confirms stock and wants it.

**Free-delivery hook:** aim for mid and large tiers to naturally clear the **5,000 TRY free-delivery threshold** so "توصيل مجاني" becomes part of the bundle pitch. Enes to confirm the tiers actually land there once priced.

**Value message:** "طلب واحد وسفرة رمضان كلها ماشية" (one order, your whole week of iftars sorted) — convenience-first, with a soft "أوفر من إنك تشتري كل صنف لوحده" secondary cue. **Do not** use Migros-style "price-lock / fixed price" language — our prices move daily and Rule #2 forbids unconfirmed price claims. Value is framed as *bundle convenience*, not a frozen price.

---

## 7. Creative Requirements — handoff

Full brand rules live in `_context/`. Downstream agents read them at runtime. Non-negotiables apply to **every** asset (see §7.4).

### 7.1 To `content-creator` — copy, Reels, carousel

**Bundle name:** propose and lock the Arabic name ("سفرة رمضان" / "عزومة رمضان" territory — your call).

**Tier carousel — "بندل رمضان — اختار حجم عيلتك"** (primary paid asset; must follow the existing-post workaround):
- One slide per tier (٣–٤ / ٥–٦ / ٨–١٠), mid tier visually dominant / positioned as default.
- Each slide: tier name + household size (Cairo Bold, brand red `#b90f2a`), contents list with dish names, "تكفي لـ X فطور" style coverage cue, free-delivery cue on qualifying tiers.
- Cover/first slide must carry the bundle name big and a one-line convenience hook.
- Three messaging pillars present in some form: توصيل سريع لباب بيتك · الدفع عند الاستلام · طازج لباب بيتك.
- WhatsApp CTA on the final slide.
- **No prices on the carousel unless Enes confirms a price that can hold for the week** (see §8). Default to "اطلب على الواتساب وbusiness يحسبهالك" style wording if prices are not locked.

**Reels (priority format — first 3 seconds decide watch-through, strong on-screen text + explicit CTA):**
1. **"Unboxing the bundle"** — hands only, opening the delivered package on the counter, naming each cut and the dish it's for ("دي للطاجن… دي للمشاوي… دي للشوربة"). First 3s: box hitting the table + bold on-screen bundle name.
2. **"Prep / in-house butchering"** — portioning the bundle, hygiene visible, no faces. On-screen: the three pillars. This is the core trust asset.
3. **"Countdown to iftar"** — light going to sunset, table filling with dishes made from the bundle, close on WhatsApp CTA. Warm, nostalgic, not glossy.
4. **"عزومة الليلة؟"** (Phase 3) — large bundle framed for hosting: big platter, plenty for guests, "رسالة واحدة ويوصلك بكرة."
5. Weekly top-up variant (Phase 2) — "سفرة الأسبوع دي كلها بطلب واحد."

**4:5 static hook A/B test set** (see §8 for method): same bundle image/template, **vary only the hook line.** Provide at least three hooks:
- (a) convenience / time: queue-avoidance, calm-before-adhan framing
- (b) planning: "سفرة رمضان كلها بطلب واحد"
- (c) family / nostalgia: "رمضان زمان على سفرتك"

**Tone:** warm, familiar, neighbourly. Short lines. Egyptian-leaning colloquial, broadly readable. Masculine verb forms for/about Enes. Emojis in moderation.

### 7.2 To `creative-designer` — Canva / bilingual

- A Canva/bilingual (Arabic + Turkish) flyer version of the tier bundle for the Kayaşehir / Bahçeşehir flyer channel, tied to a trackable coupon code (coordinate the code with `data-analyst`).
- Any campaign-specific static ad creative that needs Brand Kit template work and is attached directly in Ads Manager.
- Brand palette: Primary Red `#b90f2a`, White `#ffffff`, Near-Black `#1a1a1a`. Cairo Bold for tier names/prices, Cairo Regular / Tajawal for body. Arabic RTL, never left-aligned.

### 7.3 What the paid carousel and the 4:5 test each need to do

- **Carousel:** communicate the whole bundle system at a glance — that there is a right-sized option for any household, what's in each, and that ordering is one WhatsApp message. It carries the *structure* and the *convenience proof*.
- **4:5 static test:** isolate which **hook angle** pulls the cheapest conversation (convenience vs planning vs nostalgia), so Phase 2/3 creative leans into the winner. It carries the *angle test*, nothing else changes between variants.

### 7.4 Non-negotiables (every asset)

- CTA is always a WhatsApp message to **+90 534 570 30 37**. No website, no checkout.
- **Never show Enes's face.** Behind-the-scenes = hands, tools, product, packaging only.
- **Never mention or imply market sourcing.** Origin questions redirect to in-house butchering, hygiene, control.
- **No price in any customer-facing asset until Enes confirms it** (Rule #2). Flag every price-bearing asset as blocked on confirmation.
- Three messaging pillars present in some form.
- Arabic renders RTL. Short conversational lines, no long paragraphs.
- No season-ending / "last chance before Ramadan's over" language — the bundle must retire cleanly after Eid.
- Run the pre-publish checklist in `_sop/sop-content-production.md` §5 before any asset is called done.

---

## 8. Success Metrics + Kill / Scale Rules

**Primary metric:** cost per WhatsApp messaging conversation.

| Metric | Healthy | Watch | Act |
|---|---|---|---|
| Cost per conversation | 25–35 TRY | 35–45 TRY — hold budget, prep creative | 45–50+ TRY → add fresh creative to the ad set and/or expand geography (SOP §5) |
| Frequency | < 2.5–3 | approaching 3 → add new creative to the same ad set (do not pause) | > 3.5–4 → expand audience geography or add 2–3 new creatives (SOP §5) |
| Conversation → order rate | per `data-analyst` reconciliation vs. real WhatsApp orders | falling while cost/conv steady = creative promising the wrong thing → revise copy | — |
| ROAS | benchmark ~14x (account history) | materially below through a full week with healthy cost/conv → basket/pricing issue, escalate to Enes | — |
| Bundle basket value | set expectation once tiers priced | — | — |

**Scale rule (SOP §4):** if cost per conversation holds **under 35 TRY** and frequency stays **under 3** for **3+ consecutive days**, raise the ad set daily budget by **10–20%**. Never more. Never by toggling the campaign off/on.

**Refresh / drop-drop response (SOP §6):**
1. Do **not** immediately pause anything. Check the cost-per-conversation trend over the last 3–5 days first.
2. Frequency high but cost/conv still acceptable → let it run, prep new creative in parallel.
3. Cost/conv rising >30% from baseline → add fresh creative to the **same ad set** immediately, don't wait.
4. A brand-new ad set (loses learning history) is a **last resort**, only after both audience expansion and creative refresh have been tried.

**Kill rules (individual ads only):**
- Pause an individual **ad** if its cost per conversation is **50+ TRY after 5–7 days of delivery** AND a fresher ad in the same set is clearly outperforming it. The ad set stays ON.
- **Never** pause the campaign or an ad set to "reset" performance (Rule #6, SOP §2 Step 5, SOP §5). This destroys Meta's learning phase.
- Bahçeşehir (Ad Set B): if cost per conversation stays **above ~50 TRY for 10+ days** despite a creative refresh, pause **that ad set's ads** and report — do not let it drag the envelope. Core and retargeting continue.

**A/B hook test method (SOP §7):**
- Test **hooks only** — same product, same template, vary the headline/angle.
- Launch each hook as a **separate single-image 4:5 ad inside the same ad set** (not multiple carousel cards).
- Run **5–7 days minimum** before judging.
- Compare via **Breakdown → By Ad** in Ads Manager.
- Feed the winning angle into Phase 2 and Phase 3 creative drops.

---

## 9. Needs Enes to Confirm BEFORE Launch

Nothing is built or scheduled until these are answered. Price-related items block any price-bearing creative regardless of campaign readiness.

1. **Bundle price per tier** (3–4 / 5–6 / 8–10 people) — set against current daily cost.
2. **Price-hold feasibility** — can a bundle price hold stable for a **full week at a time** given daily cost movement? This determines whether any price can appear in creative at all, or whether all copy stays "اطلب على الواتساب" with no number.
3. **Ramadan-volume stock** — are ريش (ribs), فخذ / كتف (lamb leg / shoulder), and عظم للشوربة / رقبة (soup bones / neck) available at Ramadan volume? They cannot be named in a fixed bundle otherwise.
4. **Exact cut mix + per-tier weights** — finalise against stock and cost (research anchor: ~2.5–3.5 / ~4.5–6 / ~8–10 kg).
5. **Free-delivery threshold** — do the mid and large tiers, once priced, clear **5,000 TRY** so free delivery can be part of the pitch?
6. **Suhoor add-on** (مفروم / كبدة / سجق) — include it or not?
7. **Charity / "sponsor a table" beat** — run it or not? Include **only** if it can be delivered for real; a faked charity beat is off the table.
8. **Ramadan 2027 start date** — reconfirm by moon sighting in January; the whole phase calendar shifts with it.
9. **Budget envelope + scope sign-off** — core only (~28k TRY) / + Bahçeşehir + retargeting (~47k TRY) / + Lookalike (~53k TRY). Which scope is funded?
10. **Paying-customer phone list** — provide it (with `data-analyst`) so the Custom Audience can be built for retargeting exclusion, and confirm whether it is large enough to seed a Lookalike.
11. **Flyer coupon code** — approve a trackable code for the bilingual flyer variant.

---

## 10. Pre-Launch Checklist (to complete at build time — currently PLANNING, not launched)

From `_templates/campaign-launch-checklist-template.md`. Reproduced here so the January build has it inline; every box is currently **unchecked** because nothing is live.

**Campaign name:** `QUDS - Ramadan Iftar Bundle - Sales/WA - 2027`
**Planned build date:** 15–19 Jan 2027

**Pre-Launch**
- [ ] Objective set to OUTCOME_SALES (not Engagement)
- [ ] Destination set to WhatsApp only
- [ ] Targeting: correct delivery zone(s) per ad set, Arabic language, no interest layers
- [ ] Budget set (300 TRY/day on Ad Set A; flat test budgets on B/C/D per §4)
- [ ] Dayparting configured (sunset–late evening) on ad sets from Phase 2 onward
- [ ] Each carousel / Messaging-objective creative published as an organic Page post first
- [ ] Ads created via "Use Existing Post" in Ads Manager UI
- [ ] CTA set to "Send WhatsApp Message" (+90 534 570 30 37)
- [ ] Creative reviewed against Quality Checklist (`sop-content-production.md`): logo visible, price accurate/current or absent, watermark clear of product, CTA + WhatsApp number present, trust signals included, no market-sourcing mention, Arabic RTL correct
- [ ] "Needs Enes to confirm" list (§9) fully cleared
- [ ] Custom Audience built for retargeting exclusion (or Ad Set C shelved)
- [ ] Pre-launch `data-analyst` performance snapshot reviewed; starting budget + cost/conv target re-anchored to live numbers

**Launch**
- [ ] Adding new ads to the existing ad set — NOT pausing it
- [ ] Ads turned ON
- [ ] Any ad being replaced set to OFF individually — ad set stays ON

**Post-Launch (Day 1–3)**
- [ ] Confirm ads delivering (not stuck in review / rejected)
- [ ] Note baseline cost per conversation per ad for coming-days comparison

---

## 11. Campaign Log

| Date | Action | Entity | ID | Reason / notes |
|---|---|---|---|---|
| 2026-09-06 | Brief written (planning only) | Campaign: `QUDS - Ramadan Iftar Bundle - Sales/WA - 2027` | not created | Ramadan 2027 seasonal push. No live Meta object created. Awaiting Enes confirmations (§9), downstream creative, and a January pre-launch data snapshot. |

Future sessions: append every campaign / ad set / ad created or paused here (name, ID, reason) so `data-analyst` and later strategists have the history.

---

## 12. Downstream Handoff Order

1. **Enes** — clear §9 (prices, stock, scope, dates, charity call).
2. **`data-analyst`** — January pre-launch performance snapshot into `reports/`; assemble paying-customer list with Enes.
3. **`content-creator`** — bundle name, all copy, Reels scripts, tier carousel, 4:5 hook set (this brief + `_context/` + `_sop/sop-content-production.md`).
4. **`creative-designer`** — bilingual flyer variant, any Canva ad creative.
5. **`campaign-strategist`** (next session) — build campaign + ad sets PAUSED via API, run the existing-post workaround, complete §10 checklist, take ads live on 20 Jan 2027, manage phasing/scaling/refresh through the 10–12 Mar wind-down.
