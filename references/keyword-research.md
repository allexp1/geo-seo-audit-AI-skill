# Keyword Research — Modern Methodology

Keyword research in 2026 is different from 2016. Volume numbers are less meaningful (AI Overviews intercept many queries pre-click), intent matters more than headcount, and the buyer now asks conversational questions. This guide reflects that.

## Mental model

Don't start with "what keywords have high volume?" Start with:

1. **Who is my buyer?** (specific persona, not "everyone")
2. **What problem are they trying to solve?**
3. **How would they phrase the problem in 2026?** (conversational, not telegraphic)
4. **What does success look like?** (a sale, a sign-up, a specific behavior)

Every keyword worth targeting should connect to a specific answer to #4.

## Intent classification

Every keyword fits one of four buckets. Target commercially if your goal is revenue.

| Intent | Example | You should target if |
|--------|---------|---------------------|
| Informational | "what is CPaaS" | You want top-of-funnel / authority |
| Navigational | "Twilio login" | Never — it's brand search for a specific site |
| Commercial | "best SIP trunking provider for voice AI" | Yes — high buyer intent |
| Transactional | "buy German DID number" | Yes — highest buyer intent |

Commercial + transactional are worth 10-100× informational for most businesses. Prioritize them.

## Workflow — 6 steps

### 1. Seed from customer conversation

The best keywords come from actual customer words, not keyword tools.

Sources:
- Sales call transcripts (how did the prospect describe the problem?)
- Customer support tickets
- Reddit / forum / Hacker News threads in your category
- App Store / G2 / Capterra review content for you + competitors
- Your own Gong / Fireflies recordings
- LinkedIn posts where your ICP complains about their problem

Extract 20-40 seed phrases in the buyer's exact words.

### 2. Expand with tools

Put seed phrases through:
- **Google Autocomplete** — free, real-time intent signal
- **Google Search Console** — already-working queries for your site
- **Ahrefs / Semrush / Moz** — paid, comprehensive
- **AlsoAsked / AnswerThePublic** — free-ish, good for PAA-intent
- **Keyword Surfer** (free Chrome ext) — volume + CPC inline on Google SERPs
- **Perplexity / ChatGPT itself** — "if I were looking for X, what would I search?"

Expand to ~200–500 candidate phrases per topic cluster.

### 3. Score each candidate

Four metrics, rough quarterly/monthly data:

| Metric | Source | What it tells you |
|--------|--------|-------------------|
| Monthly search volume | Ahrefs / Semrush / Google Keyword Planner | Raw demand |
| Keyword difficulty (KD) | Ahrefs / Semrush | How hard to rank |
| Cost-per-click (CPC) | Google Keyword Planner | Commercial value |
| AI Overview presence | Manual SERP check | If AIO shows, clicks drop 30-50% |

**Shortcut formula** (not perfect but fast):

```
score = (volume × CPC × intent_multiplier) / (difficulty × aio_penalty)

intent_multiplier: informational=0.5, commercial=1.5, transactional=2.0
aio_penalty: no AIO=1.0, AIO present=1.5
```

Sort by score.

### 4. Cluster by topic

Group keywords that should live on the same page. Ten variants of "SIP trunking provider" don't need ten pages — they need one excellent page.

Clustering rule: two keywords belong on the same page if Google shows largely overlapping top-10 results for both.

Use Keyword Insights, Clusterly, or do it manually with the top-10 URL comparison.

### 5. Map clusters to content

For each cluster, assign:
- **Primary keyword** (highest score, drives the URL/title)
- **Secondary keywords** (2–5, drive H2s and body)
- **Target URL** (new page or refresh existing)
- **Intent** (informational → blog, commercial → product/category page, transactional → landing/pricing)
- **Content type** (guide, comparison, directory, tool, video, FAQ)
- **Quarter to ship**

### 6. Validate with competitor SERP analysis

Before writing, check who already ranks. For each target keyword:

- Top 10 results — blog posts? product pages? Reddit? YouTube? Quora?
- AI Overview? What does it say? From which sources?
- Featured snippet? Format (paragraph / list / table)?
- People Also Ask? Note the questions

**If Reddit / forums dominate top 10:** you're competing against authentic user content. Your page needs real data or strong expertise, not just "better writing."
**If AI Overview dominates:** traffic will be low regardless of your rank. Optimize the page for being cited in the AIO (structured answer, schema, authoritative tone) rather than for clicks.
**If YouTube dominates:** the intent may be visual. A text page may underperform.

## 2026-specific patterns

### Conversational queries

Old: `"project management software"` (2 words, telegraphic)
New: `"best project management software for remote teams of 15 on a 500 dollar monthly budget"` (natural language, multi-constraint)

Tools matter less here — real users and AI chatbots will surface these phrasings. Target them in H3 questions and FAQ schema.

### Zero-click queries

Many queries now return an AI Overview or SGE-style answer with no click needed. If your buyer persona's top queries are zero-click, don't target them for traffic — target them for *citation* (see `ai-visibility-testing.md`).

Rule of thumb:
- If CTR on the query is >8% → click game, write for clicks
- If CTR is <4% → citation game, write for AI extraction

### Long-tail surge

2023-2024 saw long-tail query volume grow ~2× faster than head-term volume, partly because conversational AI made longer queries normal. Target long-tail aggressively.

### Branded + informational hybrid

`"DIDWW pricing"` — branded
`"SIP trunking pricing"` — informational
`"DIDWW vs Twilio pricing"` — hybrid, very high intent

The hybrid bucket is underserved by most competitors. Easy wins.

## Common pitfalls

- Chasing high-volume head terms you can't rank for → invest 6 months, rank position 30, zero traffic
- Ignoring intent → ranking #1 for "what is X" doesn't make money
- Volume-only scoring → misses commercial value (low-volume high-CPC B2B often beats high-volume low-CPC consumer)
- Not checking AIO → content optimized for clicks on a query where clicks don't happen
- Over-clustering → one giant page fails to rank for any single query
- Under-clustering → ten mediocre pages instead of one great one

## Keyword research output — what deliverable looks like

A single spreadsheet per topic cluster:

| Col | Example |
|-----|---------|
| Cluster | SIP trunking for voice AI |
| Primary KW | best sip trunking for voice ai agents |
| Volume | 480/mo |
| KD | 42 |
| CPC | $18 |
| AIO present | Yes |
| Intent | Commercial |
| Target URL | /solutions/voice-ai-infrastructure |
| Content type | Comparison + product landing |
| Secondary KWs | sip trunk for vapi, elevenlabs sip provider, voice ai phone number api |
| Top 3 ranking | Telnyx, Twilio, Bandwidth |
| Notes | Telnyx ranks #1 w/ dedicated landing; beat them with EU compliance angle |
| Q to ship | Q2 2026 |

20–50 rows per quarterly plan is plenty. Ship them, measure, iterate.
