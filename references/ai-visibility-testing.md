# AI Visibility Testing — Methodology

Optimizing for AI citations without measuring them is the same mistake most "prestige" brands make — claiming without evidence. This file is the measurement layer of the GEO/AEO workflow.

## The core question

> *"When a likely buyer asks ChatGPT / Claude / Perplexity / Gemini a commercial question in our category, does our brand surface — and in what context, against which competitors, with what sentiment?"*

If the answer is "we don't know," the rest of the AEO work is unfalsifiable.

## Workflow

1. Build a **prompt set** of 15–30 commercial queries in the buyer's voice
2. Build a **competitor list** of 3–6 direct / adjacent competitors
3. Run `scripts/ai-citation-test.mjs` with the prompt file, brand, domain, and competitors
4. Capture output JSON with timestamp
5. Compare **against prior run** to track delta
6. Feed findings into the audit PDF (AI Visibility Scorecard section)

## Building the prompt set

Aim for 15–30 prompts that reflect how a *real buyer* asks an AI for help — not how SEO people pick keywords. Categories:

### 1. Category / "best X for Y" prompts (~8-12)

```
best global SIP trunking provider for AI voice agents
cheapest DID number provider in Germany
EU data-residency voice API for regulated industries
best interval timer app for boxing training on iOS
tempo-matching running music app that works offline
professional makeup artist directory with verified credentials
AI business idea validator for startup founders
```

### 2. Comparison prompts (~4-8)

```
DIDWW vs Twilio for enterprise SIP trunking
Telnyx or Bandwidth for voice AI infrastructure
PaceDJ vs FitBeat Music for workout tempo matching
```

### 3. Problem-framed prompts (~3-5)

```
how do I pick a SIP trunking provider for my voice AI startup
which interval timer app has the best music integration
how do I verify a makeup artist's credentials before hiring
```

### 4. Decision-criteria prompts (~3-5)

```
what should I look for in a global DID number provider
what features matter in a tempo-matching running app
what makes a professional makeup directory trustworthy
```

### Avoid

- Navigational prompts (`"DIDWW website"`) — low signal, high match rate by definition
- Single-word queries (`"SIP trunking"`) — too broad to be actionable
- Fiction-seeking prompts (`"write me a poem about..."`) — wrong mode
- Pure technical prompts (`"what is CPaaS"`) — category-education, not purchase-intent

### Prompt file format

`prompts.txt`:

```
# Category prompts
best global SIP trunking provider for AI voice agents
cheapest DID number provider in Germany
EU data-residency voice API for regulated industries

# Comparisons
DIDWW vs Twilio for enterprise SIP trunking
Telnyx or Bandwidth for voice AI infrastructure

# Problem-framed
how do I pick a SIP trunking provider for my AI voice startup
```

Lines starting with `#` are comments. Empty lines are ignored.

## Running the script

```bash
# Set at least one API key
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
export PERPLEXITY_API_KEY=pplx-...
export GEMINI_API_KEY=...

# Run the test
node scripts/ai-citation-test.mjs \
  --brand="DIDWW" \
  --domain="didww.com" \
  --competitors="Twilio,Bandwidth,Telnyx,Sinch,Plivo" \
  --prompts=prompts-didww.txt \
  --output=reports/didww-$(date +%F).json
```

The script outputs one line per query as it runs, then a summary:

```
[openai] best global SIP trunking provider for AI voice agents ... ✗ brand missing · competitors: Twilio, Telnyx
[anthropic] best global SIP trunking provider for AI voice agents ... ✓ brand mentioned 2× (positive)
...

================ SUMMARY ================
Brand: DIDWW (didww.com)
Queries: 90
Brand mention rate: 22.2%
Domain citation rate: 8.9%
Sentiment: {"positive":14,"neutral":6,"negative":0,"not-mentioned":70}
Competitor mention rates:
  Twilio: 78.9%
  Bandwidth: 56.7%
  Telnyx: 72.2%
  Sinch: 42.2%
  Plivo: 35.6%

Report written to: reports/didww-2026-04-18.json
```

## Interpreting results

### The four numbers that matter

| Metric | Healthy | Concerning | Broken |
|--------|---------|------------|--------|
| Brand mention rate | >60% | 20–60% | <20% |
| Domain citation rate | >30% | 10–30% | <10% |
| Sentiment positive share | >60% of mentions | 30–60% | <30% |
| Gap to top competitor | within 20% | 20–50% | >50% |

These thresholds are rough heuristics, not absolutes. A niche B2B brand can be "healthy" at 30% mention rate if their 5 competitors are evenly split. A consumer product needs higher numbers to justify the position.

### Common findings and what they mean

**Pattern:** Brand missing everywhere, domain never cited.
→ You are invisible to AI. Priority: get cited on Wikipedia / Wikidata, build content with schema, appear on industry list-articles, earn backlinks from authority sites. (See `knowledge-graph.md`, `topical-authority.md`.)

**Pattern:** Brand mentioned but domain never cited.
→ AI knows you exist but doesn't think your site is the authoritative source. Priority: canonical content on your own domain (not just in press), schema, `llms.txt`, authoritative internal linking.

**Pattern:** Brand mentioned but with wrong / outdated facts.
→ AI training data is stale or sourced from bad pages. Priority: fix Wikipedia / Wikidata, update LinkedIn, submit to Crunchbase, ensure your "About" page has clear, schema-annotated facts.

**Pattern:** Brand mentioned negatively.
→ Usually rooted in a specific review, news story, or Reddit thread. Priority: identify the source (it will show in the raw `text` field of the JSON), address the underlying issue, produce counter-narrative authoritative content.

**Pattern:** Provider-specific gap (e.g., strong in ChatGPT, invisible in Perplexity).
→ Different providers weight different sources. ChatGPT leans on pre-training + its web-search corpus; Perplexity leans heavily on Google results; Claude leans on a mix. Provider-specific optimization: Perplexity cares about SERP rank (do classic SEO), ChatGPT cares about Wikipedia / authoritative mentions, Claude cares about clean schema + structured content.

## Delta comparison

Run the test monthly. Compare runs:

```bash
# Run 1: March
node scripts/ai-citation-test.mjs --brand=X --prompts=p.txt --output=reports/2026-03.json

# Do AEO work.

# Run 2: April
node scripts/ai-citation-test.mjs --brand=X --prompts=p.txt --output=reports/2026-04.json

# Compare:
jq '.aggregate.overall' reports/2026-03.json reports/2026-04.json
```

Track delta in:
- Brand mention rate (absolute % change)
- Domain citation rate
- Sentiment distribution
- Competitor mention rates (are you catching up or falling behind?)

## What to include in the audit PDF

Fill the AI Visibility Scorecard section of `references/pdf-template.html` with:

- Total queries run (N prompts × M providers)
- Brand mention rate % overall
- Per-provider breakdown (table row per provider)
- Dominant sentiment (colored pill)
- Top 3 competitors cited ahead of you (with rates)
- 2-3 specific prompts where the gap is most visible (verbatim)

## Caveats — be honest about what this test can and can't tell you

- **AI models are non-deterministic.** Same prompt can produce different answers. Run 3× per prompt for stable numbers, or just accept noise and focus on directional signal.
- **Sentiment analysis is crude.** The script uses a heuristic (positive/negative words near brand mentions). For serious sentiment analysis, re-process the raw text with an LLM classifier.
- **Web-search results vary by region, user account, and time.** Results are indicative, not deterministic. Don't treat one run as gospel.
- **Provider APIs change.** If OpenAI / Anthropic / Perplexity / Gemini change their API shapes, the script will need updates. See the model-ID constants at the top of `ai-citation-test.mjs`.
- **Gemini grounding requires a paid Google AI Studio tier.** Free tier returns citations inconsistently.

## Cost estimate

A 20-prompt × 4-provider run costs approximately:
- OpenAI gpt-4o: ~$0.30
- Anthropic Claude w/ web_search: ~$0.80 (web search calls cost extra)
- Perplexity sonar-pro: ~$0.40
- Gemini 2.0-flash: ~$0.05

Total: ~$1.50 per full run. Monthly delta tracking = <$20/year. Very cheap relative to any other AEO tooling.
