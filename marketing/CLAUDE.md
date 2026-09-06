# CLAUDE.md

Marketing team workspace for **ملحمة القدس (Quds Butchery)** — a WhatsApp-only dark store / cloud butchery delivering fresh meat in Istanbul. This is a content and operations workspace, not a code repository. Outputs are marketing deliverables: ad copy, captions, creative briefs, reports, research, and SEO material.

## Workspace Structure

| Path | Purpose |
|---|---|
| `_context/` | Brand foundation. Source of truth for voice, style, products, and growth strategy. Read before producing anything. |
| `_sop/` | Standard operating procedures per workflow (ads, content, replies, reporting). Follow the relevant SOP end to end. |
| `_templates/` | Reusable fill-in templates. Start from these rather than inventing new structures. |
| `ads/` | Ad copy, creative briefs, campaign definitions |
| `social/` | Post captions, reels scripts, comment/DM replies |
| `pages/` | Landing page and long-form page copy |
| `reports/` | Weekly/monthly performance reports |
| `research/` | Market, competitor, and audience research |
| `seo/` | Keyword and search content |

Finished outputs go in the folder matching their type — never in `_context/`, `_sop/`, or `_templates/`.

## Language — Read This First

**The business operates in Arabic. The audience is Arabic-speaking.**

- All customer-facing output is written in **Arabic (Egyptian-leaning colloquial)**, broadly readable across Egyptian, Syrian, Jordanian, and Gulf dialects. Not فصحى — formal classical Arabic reads as distant and stiff here.
- **Turkish** is the secondary language: Turkish-speaking commenters, and bilingual materials like flyers. Match the customer's language when replying.
- Arabic must render right-to-left. Never left-align Arabic body text.
- English is for internal working documents only (briefs, reports, research) — never for customer-facing copy.
- Write short, conversational lines. Long unbroken paragraphs do not fit this brand.

## Loading Context

Always load `_context/brand-voice-guide.md` and `_context/brand-content.md` — they govern every customer-facing output. Load the rest when directly relevant:

| Task | Also load |
|---|---|
| Captions, ad copy, comment replies | `_sop/sop-content-production.md`, `_sop/sop-comment-and-dm-replies.md` |
| Anything visual, creative direction, Canva work | `_context/brand-style-guide.md` |
| Anything naming a product or price | `_context/product-offerings.md` |
| Campaign setup, budget, targeting, performance | `_context/growth-marketing-context.md`, `_sop/sop-meta-ads-campaign-management.md` |
| Weekly/monthly reports | `_sop/sop-weekly-reporting.md` |

## Non-Negotiable Rules

1. **Never mention or imply market sourcing.** No public-facing content — posts, ads, replies, DMs — may state or hint that products are bought from a market. When asked about origin, redirect to in-house butchering, hygiene, and control. This is a hard rule with no exceptions.
2. **Never publish a price without confirming it with Enes.** Prices in `_context/product-offerings.md` are a static reference baseline that goes stale — actual prices move daily/weekly. Flag any price-specific output as needing confirmation before it ships.
3. **Masculine Arabic verb forms when writing as or about Enes.** He is male; feminine forms are a real error, not a stylistic one.
4. **Every piece of content drives to WhatsApp: +90 534 570 30 37.** There is no website and no checkout. The CTA is always a WhatsApp message.
5. **Never show Enes's face** in creative direction or content concepts. Behind-the-scenes content uses hands, tools, product, and packaging only.
6. **Never propose pausing a campaign or ad set to "reset" performance.** That destroys Meta's learning phase. Add fresh creative inside the existing ad set; pause only individual underperforming ads.

## Brand Fundamentals (quick reference — full detail in `_context/`)

- **Model:** Dark store, no storefront. Order on WhatsApp → prepared fresh → delivered to the door → cash on delivery.
- **Audience:** Arabic speakers in Başakşehir, Esenyurt, Arnavutköy, Bahçeşehir.
- **The core challenge is the Trust Gap** — no physical store means every piece of content must actively supply trust signals: freshness cues, hygiene and in-house butchering, cash on delivery, real behind-the-scenes footage.
- **Three messaging pillars,** present in some form across all content: توصيل سريع لباب بيتك · الدفع عند الاستلام · طازج لباب بيتك
- **Tone:** warm and familiar like a trusted neighbor, never corporate. Confident about pricing and quality, never defensive or evasive. Emojis in moderation.
- **Palette:** Primary Red `#b90f2a`, White `#ffffff`, Near-Black `#1a1a1a`. Type: Cairo Bold for hooks/prices, Cairo Regular or Tajawal for body.

## Delegating to Sub-Agents

Five sub-agents live in `.claude/agents/`. Each has a narrow, non-overlapping role and pulls brand facts from `_context/` at runtime. Route to one only when the task is genuinely agent-shaped; otherwise do it directly.

### When NOT to delegate

Do the work yourself — no sub-agent — when the task is a **single, specific action that one skill or a direct edit can complete**:

- A one-off caption, single ad variation, one comment/DM reply, a quick copy tweak or proofread → handle directly (load `_sop/sop-content-production.md` or `_sop/sop-comment-and-dm-replies.md` and write it).
- "Reply to this comment," "fix this line," "shorten this caption," "translate this to Turkish," "what does the SOP say about X" → direct.
- Rendering one carousel from copy that already exists and is approved → invoke the `social-creative-designer` skill directly.
- Reading a saved report/research file and answering a question about it → direct.

### When TO delegate

Route to a sub-agent when the task is **open-ended, spans multiple skills, or needs the agent to synthesize inputs and make decisions across steps** — and dispatch matches the request:

| Route to | When the request is | Not for |
|---|---|---|
| `market-researcher` | Research competitors, market conditions, pricing benchmarks, audience/cultural signals, or platform/format trends — anything needing external web research synthesized into recommendations. Output lands in `research/`. | Writing copy, design, campaign decisions, changing the pricing file. |
| `data-analyst` | Pull and interpret Meta performance data, benchmark against baselines, reconcile ad results vs. real orders, produce the weekly report. Output lands in `reports/`. | Any change to a live campaign; copy; creative; comment replies. |
| `campaign-strategist` | Decide what to promote and when, turn that into a campaign plan (objective, audience, budget, timeline), and create/update/activate/pause campaigns, ad sets, ads, or budgets per SOP. The **only** agent that touches live campaigns. Briefs land in `ads/`. | Writing final copy; designing the asset; pulling raw data (consumes `data-analyst`'s saved report). |
| `content-creator` | Turn one brief/goal into content across whichever formats it needs — captions, posts, short-form scripts, lead magnets, page copy — **and** produce finished rendered social carousels/graphics end to end via the `social-creative-designer` skill. | Campaign/budget management; performance data; Canva template work; live comment/DM replies. |
| `creative-designer` | Canva-based creative only — Brand Kit template work, one-off/physical/bilingual designs, campaign-specific ad creative attached in Ads Manager. | Standard rendered social carousels/graphics (that's `content-creator`); strategy; final captions. |
| `community-manager` | A **batch/queue** of comments or DMs to work through — classify each against the approved reply library in `_sop/sop-comment-and-dm-replies.md`, draft language-matched replies, flag escalations to Enes. | A single reply (do it directly); campaign strategy; original marketing copy; creative. |

### Orchestration notes

- Agents **cannot invoke each other.** They hand off through saved files: `market-researcher` → `research/`, `data-analyst` → `reports/`, `campaign-strategist` → briefs in `ads/`, consumed downstream. When a workflow needs several agents (e.g. research → report → campaign plan → copy → creative), dispatch them in sequence yourself and pass each one the path to the prior output.
- A full campaign launch is multi-agent: `campaign-strategist` writes the brief, `content-creator` writes copy + carousel, `creative-designer` handles any Canva-specific asset, `campaign-strategist` puts it live.
- If the right agent's expected input file doesn't exist yet, either run the upstream agent first or tell the user it's missing — don't have the downstream agent invent the data.

## Writing Skills and Agents for This Project

Skills and agents in this workspace must be **brand-agnostic and reusable**:

- Define the **workflow and process only**. Never hardcode brand names, products, prices, phone numbers, colors, delivery zones, or account IDs into a skill or agent file.
- Skills and agents **pull brand context from `_context/` at runtime**. Reference the files by path and let the content live there — so the same skill works for another brand by swapping the context directory.
- Give each agent a **clear, non-overlapping role.** Overlapping responsibilities produce conflicting output.
- When brand-specific detail is needed, the skill instructs the agent to read the relevant `_context/` file — it does not restate the detail itself.

## Working Conventions

- Markdown for all deliverables.
- Descriptive kebab-case filenames with a date prefix where the output is time-bound: `2026-09-04-weekly-ads-report.md`, `ribs-discount-carousel-brief.md`.
- Start from the matching `_templates/` file when one exists.
- Run the pre-publish checklist in `_sop/sop-content-production.md` §5 before calling any customer-facing content done.
- When a fact needed for an output isn't in `_context/` — a current price, a live campaign result, a stock level — ask rather than inventing a plausible value.
