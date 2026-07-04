# geo-seo-audit

A Claude Code skill that audits any website for **SEO** (traditional search), **GEO** (AI search — ChatGPT, Perplexity, Claude, Google AI Overviews) and **AI-agent readiness** (can browsing/shopping agents actually read and operate the site). Includes the external **ora.ai Agent Readiness score**. Outputs markdown reports or professional PDF reports with competitive analysis, keyword rankings, and a 90-day action plan.

Checks are current to **mid-2026**: Lighthouse Agentic Browsing, Cloudflare's default AI-crawler blocking and Content-Signal, the post-May-2026 rich-results landscape (FAQ/HowTo retired), the 2026 AI crawler roster (OAI-SearchBot, Claude-SearchBot, OAI-AdsBot, Meta-ExternalFetcher, …), MCP/NLWeb/OpenAPI discovery, and Web Bot Auth.

**And it stays current.** Domain facts live in `KNOWLEDGE.md` (with a `last_updated` stamp), not in the methodology. When the skill runs and the knowledge base is older than its review interval (14 days), it offers to refresh itself: web-searching the trusted sources in `sources.md`, updating `KNOWLEDGE.md`, and logging every change to `CHANGELOG.md`. The refresh never edits methodology or code — script-constant updates are proposed to you for approval. Run it on demand with `/geo refresh`.

---

## What it does

| Command | Output |
|---|---|
| `/geo audit <url>` | Full markdown report — GEO + SEO + AGENT scores, breakdowns, keyword rankings, readability, ora.ai score, three prioritized action lists |
| `/geo pdf <url> --keywords kw1,kw2` | Professional multi-page PDF with score gauges, agent-readiness section, ora.ai section, competitive analysis, strategic roadmap, 90-day timeline |
| `/geo agent <url>` | **AI-agent readiness**: no-JS content, semantic landmarks, labeled forms, accessible names, MCP/NLWeb/OpenAPI interfaces, markdown negotiation, bot-wall detection — with owner recommendations |
| `/geo ora <url>` | External ora.ai Agent Readiness score: grade, 5-layer breakdown, top remediation recommendations (free API, no key) |
| `/geo onpage <url>` | On-page SEO: title/meta length, headings, Open Graph, Twitter Card, viewport, lang, charset, alt coverage, link counts, word count, snippet controls |
| `/geo technical <url>` | Technical SEO: HTTPS, 6 security headers, compression, response time, sitemap.xml, caching, Cloudflare fingerprint |
| `/geo crawlers <url>` | Robots.txt status for ~23 current AI crawlers with category (search / user-fetch / training), stale-token flags, Content-Signal lines |
| `/geo citability <url>` | Per-passage citation-readiness scoring + answer-first structure check |
| `/geo schema <url>` | JSON-LD detection + field completeness + deprecated rich-result flagging |
| `/geo llmstxt <url>` | Check `/llms.txt` + `/llms-full.txt` or generate a starter template |
| `/geo keywords <url>` | Extract keywords + check Google rankings |
| `/geo readability <url>` | Flesch-Kincaid, Gunning Fog, AI citation readability |
| `/geo performance <url>` | Lighthouse score + Core Web Vitals via PageSpeed Insights |

---

## Install

### 1. Clone the repo

```bash
git clone https://github.com/allexp1/geo-seo-audit.git
cd geo-seo-audit
```

### 2. Run the installer

```bash
./install.sh
```

This copies `SKILL.md`, `scripts/`, and `schema/` into `~/.claude/skills/geo/`. Nothing else is touched.

### 3. Install Python dependencies

```bash
python3 -m pip install -r requirements.txt
```

Or with a venv:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### 4. Restart Claude Code

The skill is loaded on startup. After restarting, try:

```
/geo audit https://example.com
```

---

## API Keys (optional but recommended)

Set these in your `~/.zshrc` (or `~/.bashrc`):

| Variable | Purpose | How to get |
|---|---|---|
| `SERPAPI_KEY` | Real Google keyword rankings | Free 100/month at [serpapi.com](https://serpapi.com) |
| `GOOGLE_CSE_KEY` + `GOOGLE_CSE_CX` | Google Custom Search API | Free 100/day via [Google Cloud Console](https://console.cloud.google.com) |
| `PAGESPEED_API_KEY` | Higher PageSpeed Insights limits | Free at [Google Cloud Console](https://console.cloud.google.com) |

Without any keys, keyword rankings fall back to DuckDuckGo (still useful, just not Google). The ora.ai API needs no key.

```bash
# Add to ~/.zshrc
export SERPAPI_KEY="your-key-here"
```

---

## ora.ai integration

[ora.ai](https://ora.ai) scans domains and scores 0-100 how well AI agents can
discover, understand, access, transact with, and operate a site — with a public
methodology and per-check remediation advice. The skill reads its free API:

```bash
python3 scripts/ora_score.py example.com          # cached score only (safe)
python3 scripts/ora_score.py example.com --scan   # request a fresh scan
```

**Privacy note:** a fresh scan publishes the domain on ora.ai's public
leaderboard, so `--scan` is opt-in and never run automatically.

---

## PDF Reports

Generate professional PDF audit reports with competitive analysis:

```bash
# Auto-extract keywords from the page
python3 scripts/generate_pdf.py https://example.com report.pdf

# Target specific keywords
python3 scripts/generate_pdf.py https://example.com report.pdf \
  --keywords "wholesale SIP trunking,virtual phone numbers,DID provider"
```

The PDF includes:
- Score gauges (Composite, GEO, SEO, Agent, Lighthouse)
- Full on-page and technical SEO details
- AI Agent Readiness — what the owner should do for AI agents
- ora.ai external score with layer breakdown
- Keyword extraction + Google rankings
- Competitive analysis per keyword: who ranks #1-3, what they do right, how to outrank them
- Keyword opportunity matrix (difficulty + recommended action)
- 3-tier content strategy (quick wins / new pages / long-term investment)
- GEO strategy for AI citations
- 90-day action timeline

---

## Use scripts standalone (no Claude needed)

Every script is self-contained — takes a URL, prints JSON (or markdown for `report.py`):

```bash
python3 scripts/report.py https://example.com > report.md
python3 scripts/crawler_check.py https://example.com | jq
python3 scripts/agent_readiness.py https://example.com | jq
python3 scripts/ora_score.py example.com | jq
python3 scripts/citability.py https://example.com | jq
python3 scripts/keyword_extract.py https://example.com | jq
python3 scripts/keyword_rank.py example.com "keyword one" "keyword two" | jq
python3 scripts/keyword_rank.py example.com --from-extract https://example.com | jq
python3 scripts/readability.py https://example.com | jq
python3 scripts/onpage_seo.py https://example.com | jq
python3 scripts/technical_seo.py https://example.com | jq
python3 scripts/performance.py https://example.com mobile | jq
```

---

## Layout

```
geo-seo-audit/
├── SKILL.md                # Claude Code skill definition (methodology + refresh protocol)
├── KNOWLEDGE.md            # mutable domain facts (crawler roster, deprecations, thresholds)
├── sources.md              # trusted sources for the refresh protocol (review once!)
├── CHANGELOG.md            # audit log of knowledge refreshes
├── install.sh              # plain cp into ~/.claude/skills/geo
├── requirements.txt        # requests, beautifulsoup4, ddgs, google-search-results, reportlab
├── scripts/
│   ├── fetch_page.py       # HTML + metadata fetcher
│   ├── onpage_seo.py       # title, meta, OG, Twitter, viewport, alts, links, snippet controls
│   ├── technical_seo.py    # HTTPS, security headers, sitemap, response time, Cloudflare
│   ├── crawler_check.py    # robots.txt vs ~23 current AI bots + Content-Signal + stale tokens
│   ├── citability.py       # passage scoring + answer-first structure
│   ├── schema_extract.py   # JSON-LD detection + deprecated rich-result flagging
│   ├── llmstxt.py          # /llms.txt + /llms-full.txt check + template generator
│   ├── agent_readiness.py  # AI-agent usability: parseability, labels, interfaces, bot walls
│   ├── ora_score.py        # ora.ai Agent Readiness API client (free, keyless)
│   ├── scoring.py          # shared scoring — single source of truth for both reports
│   ├── keyword_extract.py  # keyword extraction (freq + position weighting)
│   ├── keyword_rank.py     # Google rankings (SerpAPI / CSE / DuckDuckGo)
│   ├── readability.py      # Flesch-Kincaid, Gunning Fog, AI readability
│   ├── performance.py      # Lighthouse + Core Web Vitals via PageSpeed Insights
│   ├── report.py           # orchestrator → full markdown report
│   └── generate_pdf.py     # professional PDF report with competitive analysis
└── schema/                 # JSON-LD templates to copy and fill in
    ├── organization.json
    ├── website.json
    ├── article.json
    ├── faq.json
    └── local-business.json
```

---

## Scoring

Three pillars plus a composite (their mean). The external ora.ai score is
shown alongside but not folded in.

**GEO Score (0-100) — AI search visibility:**

| Category | Weight | What it measures |
|---|---|---|
| AI Crawler Access | 30% | Category-aware: blocking search/user-fetch bots (removes you from AI answers) is heavily penalized; blocking training bots is a policy choice. Blocking Googlebot/Bingbot caps the score — it also kills AI Overviews/Copilot |
| Citability | 30% | Avg passage score (length, self-containment, fact density, answer phrasing) |
| Schema Coverage | 20% | JSON-LD presence, high-value types, Organization `sameAs` entity linking |
| llms.txt | 10% | Present and well-formed (+ llms-full.txt) |
| Answer-First Structure | 10% | Citable passage in the first 30% of content + comparison tables/lists |

**SEO Score (0-100) — traditional search:**

| Category | Weight | What it measures |
|---|---|---|
| On-Page SEO | 50% | Title, meta, H1, canonical, OG, Twitter, viewport, lang, charset, alt, links |
| Technical SEO | 50% | HTTPS, security headers, compression, speed, sitemap, caching |

**AGENT Score (0-100) — AI-agent usability (new):**

| Category | Weight | What it measures |
|---|---|---|
| Content parseability | 35% | Meaningful text without JS, text-to-markup ratio, semantic landmarks, heading hierarchy |
| Interaction readiness | 25% | Labeled form fields, accessible names on buttons/links, no div-soup click targets, WebMCP |
| Agent interfaces | 25% | llms.txt, MCP discovery, OpenAPI, api-catalog, Web Bot Auth keys, NLWeb, markdown negotiation |
| Access | 15% | Bot-wall detection (browser UA vs AI-bot UA comparison) |

**Additional sections (shown but not in composite):**

| Section | Source |
|---|---|
| ora.ai Agent Readiness | ora.ai free API (5 layers: Discovery, Identity, Access, Payments, Experience) |
| Keywords + Rankings | Google (SerpAPI) or DuckDuckGo |
| Readability | Flesch-Kincaid, Gunning Fog |
| Performance | Google PageSpeed Insights (LCP ≤2.5s, INP ≤200ms, CLS ≤0.1) |
| Competitive Analysis | SerpAPI top 3 per keyword |

---

## What this skill deliberately leaves out

- No `curl | bash` installer — just a plain `cp` script you can read in 10 seconds.
- No CRM, prospect tracking, or persistent data outside the skill folder.
- No paid-community funnel.
- No local brand-mention / share-of-voice tracking (ora.ai's Discovery layer covers part of it; Profound/Otterly/Peec cover the rest).
- Scripts only read, never write outside their own output. The one external call is the read-only ora.ai score; fresh ora scans are strictly opt-in (`--scan`).

---

## Limits

- **Static HTML only.** JS-rendered pages look thin to citability and schema checks — and to the AGENT parseability check, which measures exactly that on purpose.
- **No authentication.** Pages behind login walls return the public version.
- **Heuristic scoring.** Citability is a proxy, not a measurement of actual AI citations.
- **llms.txt honesty.** Google Search does not consume it; Lighthouse's agentic audit checks it and coding agents fetch it. Scored accordingly (low weight).
- **DuckDuckGo != Google.** Without SerpAPI, keyword rankings are directional.
- **PageSpeed Insights** has a daily free quota. Set `PAGESPEED_API_KEY` if you hit 429s.
- **ora.ai** rate-limits ~10 requests/min per IP; unscanned domains return no score unless you opt into a public scan.

---

## Uninstall

```bash
rm -rf ~/.claude/skills/geo
```

That's it. Nothing else was created.

---

## Requirements

- Python 3.9+
- Claude Code CLI
- Git

---

## License

MIT
