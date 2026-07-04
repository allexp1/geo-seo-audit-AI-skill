---
last_updated: 2026-07-04
review_interval_days: 14
---

# GEO Skill — Domain Knowledge Base

Mutable facts the audit relies on. The Refresh Protocol in SKILL.md rewrites
sections of this file; methodology stays in SKILL.md. Every fact here was
verified against the sources in sources.md on the `last_updated` date.

## AI crawler roster

Current checkable robots.txt tokens (mirrored in `scripts/crawler_check.py:AI_BOTS`):

| Token | Vendor | Category | Notes |
|---|---|---|---|
| GPTBot | OpenAI | training | v1.2; IP list at openai.com/gptbot.json |
| OAI-SearchBot | OpenAI | search | ChatGPT search index |
| ChatGPT-User | OpenAI | user-fetch | robots.txt "may not apply" |
| OAI-AdsBot | OpenAI | ads | NEW 2025-26; validates ChatGPT ad landing pages |
| ClaudeBot | Anthropic | training | |
| Claude-SearchBot | Anthropic | search | |
| Claude-User | Anthropic | user-fetch | |
| PerplexityBot | Perplexity | search | documented circumventing robots.txt (Cloudflare, Aug 2025) |
| Perplexity-User | Perplexity | user-fetch | Perplexity says robots.txt "not required" |
| Google-Extended | Google | training | opt-out token for Gemini; does NOT affect Search or AI Overviews |
| Google-CloudVertexBot | Google | training | Vertex AI site grounding |
| GoogleOther | Google | other | research/experimental |
| Applebot | Apple | search | Siri/Spotlight + Apple Intelligence retrieval |
| Applebot-Extended | Apple | training | opt-out token, not a crawler |
| Meta-ExternalAgent | Meta | training | |
| Meta-ExternalFetcher | Meta | user-fetch | |
| Amazonbot | Amazon | search | Alexa; honors page-level `noarchive` as training opt-out |
| Bytespider | ByteDance | training | notoriously non-compliant, spoofs UAs |
| CCBot | Common Crawl | training | upstream of most open training corpora |
| DuckAssistBot | DuckDuckGo | search | explicitly not for training |
| MistralAI-User | Mistral | user-fetch | Le Chat |
| Diffbot | Diffbot | other | knowledge graph |
| YouBot | You.com | search | |

**Stale tokens** (flag if present in robots.txt): `anthropic-ai`, `claude-web`
(Anthropic retired both), `FacebookBot` (Meta legacy).

**Not controllable via robots.txt**: ChatGPT Atlas browsing (plain Chrome UA),
Perplexity Comet, Microsoft Copilot Actions (Edge UA), xAI/Grok (no documented
UA, residential IPs).

**Core-search coupling**: Googlebot feeds AI Overviews/AI Mode; Bingbot feeds
Copilot. Blocking either removes the site from those AI surfaces.

## Cloudflare and access policy

- Since July 2025 Cloudflare blocks AI **training** crawlers by default for new
  zones (~20% of the web is behind Cloudflare) — robots.txt can look permissive
  while the WAF 403s bots.
- From **2026-09-15**: mixed-use crawlers blocked by default on ad-monetized
  pages; Training + Agent categories blocked by default for new/free zones;
  Search stays allowed. "Pay Per Use" (HTTP 402) launching with Ceramic.ai and
  You.com. BotBase directory of verified bots.
- **Content Signals Policy** (Sept 2025): `Content-Signal: search=yes,
  ai-train=no, ai-input=yes` lines inside robots.txt; live on 3.8M+ domains;
  not yet an IETF standard. Parsed by `crawler_check.py`.
- **Web Bot Auth**: HTTP Message Signatures (RFC 9421) + `Signature-Agent`
  header; keys at `/.well-known/http-message-signatures-directory`; adopted by
  Cloudflare, AWS WAF, Vercel, Shopify, Akamai. IETF milestones April/Aug 2026.

## llms.txt status

- Spec: llmstxt.org (H1 name, blockquote summary, H2 link sections);
  `llms-full.txt` = full content inlined (community convention).
- ~10% adoption. No major AI vendor committed to consuming it; Google
  explicitly says Search does not use it. SE Ranking (~300k domains): no
  correlation with AI citations.
- BUT: Lighthouse's Agentic Browsing category (May 2026) checks for it, and
  coding/IDE agents (Cursor, Claude Code, Copilot) fetch it on docs sites.
- Verdict encoded in scoring: low-weight (10% of GEO) agent-readiness signal;
  always state the caveat in reports.

## Google AI features (AI Overviews / AI Mode)

- Google's consolidated AI-optimization guide (May 2026, updated 2026-06-29):
  AI features are rooted in core ranking systems; page must be indexed,
  snippet-eligible, publicly crawlable. Explicitly NOT needed: llms.txt,
  markdown versions, AI-specific markup, content chunking.
- Snippet controls (`nosnippet`, `data-nosnippet`, `max-snippet`, `noindex`)
  govern AI Overviews/AI Mode quoting. `Google-Extended` does NOT remove a
  site from AI Overviews.
- AI Mode uses query fan-out → long-tail sub-topic coverage on distinct
  crawlable URLs helps.
- Citation correlations (third-party studies, directional): ~44% of LLM
  citations come from the first 30% of page content (basis of the
  answer-first check); rank-citation link weakening (76% top-10 mid-2025 →
  ~38% early 2026 per Ahrefs); branded web mentions correlate 0.664 with AI
  Overview visibility vs 0.218 for backlinks; listicles/comparison tables win
  "best X" queries.

## Structured data status

Still supported and valuable: Product, Offer, Review/AggregateRating, Article,
Recipe, VideoObject, Organization, LocalBusiness, BreadcrumbList, JobPosting,
Event. Organization `sameAs` → entity linking (Wikipedia/Wikidata/social).

Deprecated rich results (markup still parses; no visual result — mirrored in
`scripts/schema_extract.py:DEPRECATED_RICH_RESULTS`):
- HowTo — dead since Sept 2023
- FAQ — removed May 2026 (Rich Results Test support dropped June 2026);
  FAQPage markup still aids AI parsing of Q&A content
- June 2025 batch: Book Actions, Course Info, Claim Review, Estimated Salary,
  Learning Video, Special Announcement, Vehicle Listing

## Core Web Vitals

LCP ≤ 2.5 s, INP ≤ 200 ms, CLS ≤ 0.1 — **unchanged**; INP replaced FID in
March 2024 (FID fully retired Sept 2024). Claims of 2026 threshold changes
("LCP 2.0s", "Engagement Reliability metric") circulate on SEO content farms
and are contradicted by web.dev/CrUX release notes — do not encode them.

## Agent readiness standards

- **Lighthouse Agentic Browsing** (Lighthouse 13.3, May 2026; in PSI since
  ~June 2026): accessibility-tree quality (programmatic names, valid roles),
  CLS, llms.txt presence, WebMCP form annotations. Google's framing: the
  agent-friendly checklist "is the accessibility audit restated".
- **WebMCP**: W3C Draft CG Report Feb 2026; `navigator.modelContext`; Chrome
  origin trial (Chrome 149-156, public since June 2026). Chrome-only so far.
- **NLWeb** (Microsoft, Build 2025): natural-language endpoint (`/ask`) built
  on a site's Schema.org/RSS data; every NLWeb instance is automatically an
  MCP server (`/mcp`). Adopters: Shopify, Tripadvisor, Eventbrite, O'Reilly.
- **Discovery files**: `/.well-known/mcp.json` (MCP), `/.well-known/api-catalog`
  (RFC 9727), OpenAPI at `/openapi.json` or `/api/openapi.json`, markdown
  content negotiation (`Accept: text/markdown`).
- **agents.json / ai.txt / agent-manifest.txt**: multiple competing proposals,
  none standard (W3C AI Agent Protocol CG specs expected 2026-27). Detect and
  report; don't require.
- **Agentic commerce**: ACP (OpenAI+Stripe, live Sept 2025; March 2026 pivot of
  Instant Checkout into Apps), Google AP2/UCP, x402. For e-commerce: clean
  product feed + Product schema with price/availability.

## ora.ai API

- Free, keyless read API; ~10 scans/min/IP; `Retry-After` on 429.
- `GET https://ora.ai/api/score/{domain}` → cached ScanResult (404 = never
  scanned). `POST /api/scan` runs a fresh scan and **publishes the domain on
  the public leaderboard** (that's why `--scan` is opt-in).
- Response shape: `score`, `maxScore`, `grade`, `layers[]` (Discovery,
  Identity, Access, Payments, Experience) each with `checks[]` carrying
  `status/score/maxScore/details/recommendation/estScoreGain`.
- Grades: A+ 95-100, A 86-94, B 70-85, C 48-69, D 28-47, F 0-27.
- Also: `GET /api/badge/{domain}` (SVG), MCP server at `https://ora.ai/api/mcp`.
- OpenAPI spec: https://ora.ai/api/openapi.json (v1.3.3 as of last check).

## On-page guidance numbers

- Title: 50-60 chars with entity names (30-60 still acceptable).
- Meta description: 140-160 chars, answer-aligned — doubles as AI Overview
  citation-card text; >60% get rewritten by Google.
- AI-citation readability sweet spot: Flesch 50-70 (8th-10th grade).
- Citable passage heuristics: 100-200 words, self-contained, fact-rich.

## IndexNow

Bing/Yandex/Seznam/Naver/Yep — Google still does not support it. 80M+ sites;
22% of Bing clicked URLs originate from IndexNow (Dec 2025). Relevant because
Bing feeds Copilot. Key file `{key}.txt` is arbitrary-named → not statically
checkable; recommend in report text only.

## Where facts live in code

Refresh NEVER edits scripts. When a section above changes, flag the matching
constant as a suggested code change for the user to approve:

| KNOWLEDGE.md section | Script constant |
|---|---|
| AI crawler roster | `scripts/crawler_check.py` → `AI_BOTS`, `STALE_TOKENS`, `CORE_SEARCH_BOTS` |
| Cloudflare and access policy | `scripts/crawler_check.py` → `detect_cloudflare()` note text |
| Structured data status | `scripts/schema_extract.py` → `COMMON_TYPES`, `DEPRECATED_RICH_RESULTS` |
| Agent readiness standards | `scripts/agent_readiness.py` → `WELL_KNOWN_PROBES`, WebMCP detection |
| ora.ai API | `scripts/ora_score.py` → `API`, `GRADE_SCALE`, `summarize()` |
| On-page guidance numbers | `scripts/onpage_seo.py` scoring bands; `scripts/citability.py` / `readability.py` heuristics |
| Core Web Vitals | `scripts/performance.py` docstring/labels |
| llms.txt status | `scripts/llmstxt.py` → `value_note` |
