# SOP — Meta Ads Campaign Management

## 1. Campaign Objective Selection

- **Default objective: OUTCOME_SALES**, optimized for Messaging (WhatsApp Conversations).
- Do **not** use OUTCOME_ENGAGEMENT as the default — historically it produced significantly worse cost-per-conversation for this account. Only reconsider if Sales objective performance degrades sharply and a controlled test is explicitly planned.
- Destination: **WhatsApp only**. Do not select "all message destinations" (Messenger/IG Direct) — the business only operates through WhatsApp, and spreading budget across destinations dilutes results and complicates order tracking.

## 2. Launching a New Creative — Decision Tree

**Step 1:** Is there an active Ad Set already running for this audience (same delivery zones)?
- **Yes →** Go to Step 2.
- **No →** Create new Campaign (PAUSED) → new Ad Set (PAUSED) with targeting per Section 3 → then Step 2.

**Step 2:** Publish the new creative as an organic Page post first (this avoids Meta API errors #1487891 and #1885090 that occur when attaching carousel creatives to a Messaging-objective ad programmatically).

**Step 3:** In Ads Manager, create a new Ad inside the existing Ad Set using **"Use Existing Post"**, selecting the post from Step 2.

**Step 4:** Set the CTA to **"Send WhatsApp Message."**

**Step 5:** Turn the new Ad **ON**. Do **not** pause the Ad Set or Campaign — only pause individual underperforming Ads if needed. Pausing a full Campaign/Ad Set resets Meta's learning phase and increases costs.

## 3. Audience / Targeting Standards

- Geography: Başakşehir (+2km), Esenyurt, Arnavutköy (+2km), Bahçeşehir — test new zones as separate Ad Sets before merging into the core cluster.
- Language: Arabic
- Detailed targeting (interests): **Do not add.** Location + language targeting has proven sufficient; adding interest layers narrows the audience unnecessarily and raises cost.
- Estimated audience size reference: ~220,000-260,000 for the current 3-4 zone cluster.

## 4. Budget Management

- Start new campaigns/ad sets at **300 TRY/day**.
- Scale gradually: increase by 10-20% increments, not large jumps, to protect the learning phase.
- Never scale by turning campaigns off and on repeatedly — this is explicitly harmful to performance (breaks learning phase each time).

## 5. Monitoring Checklist (check every 2-3 days minimum)

| Metric | Healthy Range | Action if Outside Range |
|---|---|---|
| Cost per messaging conversation | 25-35 TRY | 45-50+ TRY → refresh creative or expand audience |
| Frequency | Under 2.5-3 | Approaching 3 → add new creative to same Ad Set (do not pause) |
| Frequency | Above 3.5-4 | Consider expanding audience geography or adding 2-3 new creatives |

## 6. When Performance Drops — Response Protocol

1. **Do not immediately pause.** Check cost-per-conversation trend over the last 3-5 days first.
2. If frequency is high but cost-per-conversation is still acceptable → let it run, prepare new creative in parallel.
3. If cost-per-conversation is clearly rising (>30% increase from baseline) → add fresh creative to the same Ad Set immediately; do not wait.
4. Only create a brand-new Ad Set (losing learning history) as a last resort, after audience expansion and creative refresh have both been tried.

## 7. A/B Testing Creatives (Hooks)

- Test different **hooks** (headline/angle) on the same product/template, not the whole design — this isolates what's actually driving performance.
- Launch each hook as a **separate single-image Ad** inside the same Ad Set (not as multiple cards in one carousel) — this allows clean per-ad performance comparison via Ads Manager breakdown.
- Run for 5-7 days minimum before judging results.
- Compare via "Breakdown → By Ad" in Ads Manager reporting.

## 8. Common API Errors — Known Issues & Workarounds

| Error | Cause | Workaround |
|---|---|---|
| `#1487891` Invalid creative for objective | Carousel creative attached programmatically to Messaging-objective ad | Publish as organic post first, attach via "Use Existing Post" in Ads Manager UI |
| `#1885090` Invalid promoted object update | Attempting to modify promoted_object on a live campaign via API | Do not edit; build a fresh campaign/ad set instead if the objective needs to change |

## 9. Changing Campaign Objective Mid-Flight

- Meta does **not** allow changing a campaign's objective after creation, even via duplication (duplicate retains original objective).
- If a different objective is needed, create a new campaign from scratch with the correct objective from the start.
