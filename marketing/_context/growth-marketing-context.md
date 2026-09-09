# ملحمة القدس — Growth Marketing Context

## Sales Funnel

Meta Ads → WhatsApp conversation or digital menu → Order (cash on delivery)

Click-to-WhatsApp is the primary conversion mechanism, alongside the digital menu (product browsing + COD ordering, no online payment/checkout). There is no separate online storefront beyond these two.

## Key Accounts

- Meta Ad Account ID: `4318851221675090`
- Meta Business ID: `1068514784536305`
- Facebook Page ID: `1190105444176095`

## Historical Performance Baseline

### Campaign Objective Learnings
- **OUTCOME_SALES with Messaging/WhatsApp optimization** is the objective that has consistently produced the best results for this business model.
- **OUTCOME_ENGAGEMENT** was tested and underperformed significantly relative to Sales objective — cost per conversation was substantially higher and conversion to actual orders was poor. Do not default to Engagement objective for this account.
- Carousel creatives + WhatsApp/Messaging objective have hit Meta API errors when created programmatically (`#1487891` Invalid creative for objective, `#1885090` Invalid promoted object update). Reliable workaround: create campaign/ad set via API, publish creative organically as a Page post, then attach the ad manually in Ads Manager using "Use Existing Post."

### Documented Results (reference baselines)

| Period | Spend | Orders / Conversations | Notes |
|---|---|---|---|
| Eid al-Adha campaign (~5 days, new account) | 872 TRY | 46 tracked conversations (~60 actual orders incl. organic) | First campaign, narrow audience, brand new ad account |
| 21 Jul – 4 Sep window | 8,400 TRY | 120,000 TRY total sales (incl. DM/retargeting orders) | ROAS ≈ 14.3x |
| Profit margin | ~20-25% average | | Fuel and personal effort factored in as real costs on top of ad spend |
| Cost per messaging conversation (healthy range) | ~25-35 TRY | | Above ~45-50 TRY is a signal to refresh creative or expand audience |

### Frequency Guidance
- Frequency below ~2.5-3 is generally safe.
- Frequency climbing quickly (e.g., within 4-7 days) alongside rising cost-per-conversation is the signal to add fresh creative to the same ad set — not to pause the ad set or start over.
- Never pause a full campaign/ad set to "reset" — this destroys Meta's learning phase data. Add new ads within the same ad set and pause only underperforming individual ads.

## Growth Goals (reasonable, phase-appropriate targets)

### Short-term (next 4-8 weeks)
- Maintain cost per messaging conversation under ~35 TRY as ad spend scales up.
- Grow daily ad budget gradually (10-20% increments) rather than large jumps, to protect the learning phase.
- Build a Custom Audience + Lookalike Audience from actual paying customers to improve targeting quality.
- Launch and stabilize a monthly bilingual (Arabic/Turkish) flyer distribution in Kayaşehir, tied to a trackable coupon code, to complement (not replace) Meta Ads.
- Establish a lightweight retargeting flow: re-engage people who messaged but did not order.

### Medium-term (next 2-4 months)
- Expand delivery/marketing coverage to Bahçeşehir as a distinct ad set, testing performance separately from the core Başakşehir/Esenyurt/Arnavutköy cluster.
- Build a customer retention flow: post-purchase WhatsApp follow-ups, occasional loyalty offers for repeat customers.
- Start collecting customer feedback videos (via coupon incentive) as organic trust-building content and potential ad creative.
- Explore a simple automated FAQ response system for common WhatsApp/comment questions (pricing structure, delivery areas, cash on delivery) to reduce manual reply load.

### What Growth Should NOT Look Like
- Do not chase Engagement-objective campaigns for volume — historically this has not converted to real sales for this business.
- Do not treat flyer distribution as a replacement for Meta Ads; the two channels serve complementary purposes (broad local awareness vs. continuous, measurable digital reach with retargeting capability).
- Avoid discount language that implies permanence (e.g., wording tied to a specific ending holiday/season) once that specific promotional window has passed.

## Reporting Cadence
- Weekly: cost-per-conversation trend check per active ad, frequency check, budget pacing.
- Monthly: compare flyer-driven coupon redemptions against Meta Ads performance in the same geographic zone to evaluate combined channel effect.
