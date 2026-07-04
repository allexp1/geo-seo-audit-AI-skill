---
name: geo
description: Audit a website for traditional SEO (titles, meta, headings, Open Graph, viewport, sitemap, HTTPS, security headers, response time, compression), Generative Engine Optimization (citability scoring for ChatGPT/Claude/Perplexity/Google AI Overviews, AI crawler access incl. Content-Signal and Cloudflare defaults, JSON-LD schema with deprecated-type flagging, llms.txt), and AI-agent readiness (semantic HTML, labeled forms, MCP/NLWeb/OpenAPI interfaces, bot-wall detection, markdown negotiation) with the external ora.ai Agent Readiness score. Outputs a markdown report with GEO, SEO, and AGENT scores plus a composite and three prioritized action lists. Trigger when the user asks to audit a site for SEO, GEO, AI search visibility, AI agent readiness, agent-friendliness, llms.txt, AI crawler access, citability, technical SEO, on-page SEO, sitemap, Open Graph, schema markup, or an ora.ai score.
user-invocable: true
args:
  - name: subcommand
    description: One of audit, crawlers, citability, schema, llmstxt, onpage, technical, keywords, readability, performance, agent, ora, pdf, report, refresh. Defaults to audit.
    required: false
  - name: url
    description: The URL to analyze (https://example.com). Not needed for `refresh`.
    required: true
---

# GEO Skill

Audits a website for AI-search visibility, AI-agent usability, and the
traditional SEO signals that still matter. Outputs a prioritized markdown
report (or PDF).

The audit *methodology* lives in this file and in `scripts/`. The *domain
facts* it depends on (AI crawler roster, structured-data deprecations, CWV
thresholds, agent-readiness standards, ora.ai API details) live in
**KNOWLEDGE.md** and are kept current by the Refresh Protocol below.

## Staleness check (run first, every invocation)

1. Read KNOWLEDGE.md frontmatter.
2. If `last_updated` is older than `review_interval_days`, tell the user the knowledge base is stale and run the Refresh Protocol below before the main task.
3. If the user says "skip refresh", proceed with existing knowledge but state its age in your output.
4. Base ALL domain-specific decisions on KNOWLEDGE.md content, not on training data. When explaining findings, reference the relevant KNOWLEDGE.md section.

## Refresh Protocol

Run when the staleness check triggers, or on demand via the `refresh` subcommand.

1. Read sources.md. For each entry, web-search for changes/announcements since `last_updated`.
2. Compare findings against KNOWLEDGE.md:
   - PRIMARY-source findings: apply directly.
   - SECONDARY-source findings: apply only if confirmed by a primary source; otherwise note in CHANGELOG.md as "unconfirmed, monitoring".
3. Rewrite only the affected sections of KNOWLEDGE.md. Preserve section structure.
4. Update `last_updated` to today.
5. Append every change to CHANGELOG.md with rationale and source URL. If nothing changed, log "No changes found".
6. NEVER modify SKILL.md or sources.md during refresh. Only KNOWLEDGE.md and CHANGELOG.md.
7. Scripts are also never edited by refresh. If a change affects a script constant, consult the "Where facts live in code" section of KNOWLEDGE.md and list the needed code change in your summary as a suggestion for the user to approve.
8. Summarize to the user in 2-3 lines what changed before proceeding with their task.

## Subcommands

| Subcommand | What it does |
|---|---|
| `audit` / `report` (default) | Run **all** checks and produce the full markdown report (GEO + SEO + AGENT scores, breakdowns, three prioritized action lists) |
| `onpage` | On-page SEO only: title/meta length, headings, Open Graph, Twitter, viewport, lang, charset, alt coverage, links, word count, snippet controls |
| `technical` | Technical SEO only: HTTPS upgrade, security headers, compression, response time, sitemap.xml, caching headers, Cloudflare fingerprint |
| `crawlers` | Robots.txt analysis for the current AI crawler roster (see KNOWLEDGE.md), with category (search / user-fetch / training), stale-token flags, Content-Signal lines, core-search-bot warnings |
| `citability` | Score on-page passages for AI citation readiness + answer-first structure |
| `schema` | Detect and validate JSON-LD blocks; flag deprecated rich-result types |
| `llmstxt` | Check `/llms.txt` and `/llms-full.txt`; if missing, suggest a template |
| `agent` | **AI-agent readiness**: no-JS content, semantic landmarks, labeled forms, accessible names, MCP/NLWeb/OpenAPI/well-known interfaces, markdown negotiation, bot-wall detection — with owner recommendations |
| `ora` | External **ora.ai Agent Readiness score**: grade, layer breakdown, top remediation recommendations |
| `keywords` | Extract target keywords + check Google rankings (via SerpAPI if key set, else DuckDuckGo) |
| `readability` | Flesch-Kincaid, Gunning Fog, AI citation readability |
| `performance` | Google Lighthouse score + Core Web Vitals via PageSpeed Insights (current thresholds in KNOWLEDGE.md) |
| `pdf` | Generate a professional PDF audit report with score gauges, agent-readiness section, ora.ai section, competitive analysis, strategic roadmap, and 90-day timeline. Accepts `--keywords kw1,kw2,...` |
| `refresh` | Run the Refresh Protocol now (no URL needed) |

## How to run

All scripts live in `scripts/` next to this file. They take a URL and print JSON to stdout. From this skill's directory:

```bash
python3 scripts/fetch_page.py <url>
python3 scripts/onpage_seo.py <url>
python3 scripts/technical_seo.py <url>
python3 scripts/crawler_check.py <url>
python3 scripts/citability.py <url>
python3 scripts/schema_extract.py <url>
python3 scripts/llmstxt.py <url>
python3 scripts/agent_readiness.py <url>
python3 scripts/ora_score.py <url> [--scan]
python3 scripts/keyword_extract.py <url>
python3 scripts/keyword_rank.py <domain> <kw1> [kw2 ...]
python3 scripts/readability.py <url>
python3 scripts/performance.py <url> [mobile|desktop]
python3 scripts/report.py <url>     # runs all of the above and emits markdown
python3 scripts/generate_pdf.py <url> [output.pdf] [--keywords kw1,kw2,kw3]
```

## ora.ai integration

`ora_score.py` reads ora.ai's free, keyless API (endpoints, rate limits, and
response shape documented in KNOWLEDGE.md → "ora.ai API"). By default it only
reads the **cached** score. If the domain has never been scanned, it does NOT
trigger a scan automatically — a fresh scan publishes the domain on ora.ai's
**public leaderboard**. Ask the user before running `ora_score.py <url> --scan`.

## PDF generation

For the `pdf` subcommand, run `generate_pdf.py`. It produces a multi-page professional PDF:
- Score gauges (Composite, GEO, SEO, Agent, Lighthouse)
- Full breakdowns with auto-wrapping tables
- AI Agent Readiness section — what the owner should do for AI agents
- ora.ai external score with layer breakdown and top recommendations
- Keywords + Google rankings (via SerpAPI or DuckDuckGo)
- Competitive analysis: who ranks for each keyword, what they do right, how to outrank
- Strategic roadmap: keyword opportunity matrix, 3-tier content strategy, GEO strategy
- 90-day action timeline

Custom keywords override auto-extraction. Pass them comma-separated:
```bash
python3 scripts/generate_pdf.py https://example.com report.pdf --keywords "wholesale SIP trunking,DID number provider,virtual numbers API"
```

## Environment variables

| Variable | Purpose |
|---|---|
| `SERPAPI_KEY` | Real Google rankings (free 100/month at serpapi.com) |
| `GOOGLE_CSE_KEY` + `GOOGLE_CSE_CX` | Google Custom Search API (free 100/day) |
| `PAGESPEED_API_KEY` | Higher PageSpeed Insights rate limits |

ora.ai needs no key.

## Workflow

1. Run the staleness check (above).
2. Resolve the skill directory: `SKILL_DIR="$(dirname "$(realpath SKILL.md)")"` — or just `cd` to where this file lives.
3. Run the subcommand. For `audit` / `report`, run `report.py` which orchestrates the others.
4. Present the markdown output to the user. If individual sub-scores look concerning, suggest concrete fixes (the report already includes three prioritized action lists — SEO, GEO, AI agents — but tailor them to what you saw, citing the relevant KNOWLEDGE.md section).

## Scoring model

Three pillars, composite = their mean. The ora.ai score is shown alongside
but NOT folded in (external scale, may be missing for unscanned domains).

- **GEO** — crawlers 30% (category-aware: blocking search/user-fetch bots is
  heavily penalized, blocking training bots is a policy choice), citability 30%,
  schema 20%, llms.txt 10%, answer-first structure 10%.
- **SEO** — on-page 50%, technical 50%.
- **AGENT** — content parseability 35%, interaction readiness 25%,
  agent interfaces 25%, access/bot-walls 15%.

Weights are methodology and change only by human edit here and in
`scripts/scoring.py`. The facts behind the checks change via KNOWLEDGE.md.

## When to suggest schema templates

If `schema_extract.py` reports missing common types (Organization, LocalBusiness, Article), point the user at the matching file in `schema/` and tell them to fill in the placeholder fields. If it reports deprecated rich-result types, explain per KNOWLEDGE.md → "Structured data status".

## Scope and limits

- Static HTML only. JavaScript-rendered content is invisible without a headless browser — the AGENT pillar's parseability check measures exactly this, deliberately.
- Brand-mention / share-of-voice tracking across engines is **not** included locally — ora.ai's Discovery layer covers part of it externally; dedicated GEO measurement tools cover the rest.
- Citability scoring is heuristic, not an industry standard. It rewards passages that are 100-200 words, self-contained, and fact-rich, because those characteristics correlate with the snippets AI assistants quote. Treat scores as directional.
- llms.txt value is contested — report it with the caveat in KNOWLEDGE.md → "llms.txt status".

## What this skill does not do

- No CRM/prospect tracking. No proposal generation.
- No data is written outside this skill directory. Scripts only read.
- Never triggers an ora.ai scan without the user's explicit go-ahead (`--scan`).
