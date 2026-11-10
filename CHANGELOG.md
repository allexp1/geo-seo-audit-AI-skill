# Knowledge changelog

Audit log of every KNOWLEDGE.md change made by the Refresh Protocol. This is
the human review surface — scan new entries for ingested junk. Format:

```
## YYYY-MM-DD
- ADDED/CHANGED/REMOVED: <what> — <one-line rationale> — <source URL>
```

A refresh that finds nothing still logs `- No changes found`.

## 2026-11-11 — AgentReady v2.0 (manual update)
- ADDED: Agent readiness standards → AgentReady v2.0 rule set (ids, MUST/SHOULD/MAY, retired AR-READ-10, key study numbers) — open standard with measured basis — https://github.com/agentready-org/standard/blob/main/spec/spec.md
- CHANGED: WebMCP API object is `document.modelContext`, not `navigator.modelContext` — read in the W3C draft — https://webmachinelearning.github.io/webmcp/
- CODE: `agent_readiness.py` reports the AgentReady checklist (`agentready`), detects WebMCP on document or navigator, finds MCP servers by a read-only `initialize` handshake (also 401 + WWW-Authenticate), probes `/.well-known/ai-catalog.json`, treats 429 + Retry-After as honest throttling, and adds checks for soft 404s, linked discovery files, markdown links, homepage JSON-LD, sitemap-in-robots and pricing text. AGENT score weights unchanged. Offline tests in `tests/test_agentready.py`.

## 2026-07-04
- ADDED: Initial knowledge base, seeded from the v2 refactor research (AI
  crawler roster, Cloudflare policy, llms.txt status, Google AI-features
  guidance, structured-data deprecations, CWV thresholds, agent-readiness
  standards, ora.ai API, on-page guidance numbers, IndexNow) — all facts
  verified against the PRIMARY sources listed in sources.md on this date.

## 2026-08-24 — Refresh (triggered by staleness: 51 days since 2026-07-04)

**ora.ai API — breaking (PRIMARY: https://ora.ai/api/openapi.json)**
- Spec version v1.3.3 → **v1.20.1**. Audit scoring layers changed from the
  five-name set (Discovery, Identity, Access, Payments, Experience) to **four**:
  Discovery, Accessibility, Usability, Payments. The five-name set still exists
  but is the *journey* taxonomy, and the spec states the two must never be
  mapped onto each other.
- Rate limits are now explicit: 10 req/min/IP burst, 30 scans/rolling 24 h,
  6 force scans/24 h; API keys bypass scan-family limits.
- New endpoint families recorded (discover, journey, ard, scan/stream,
  scan/checks, checks, feedback/check).
- Grade bands not restated in the fetched spec — kept, marked unconfirmed.
- ⚠️ SUGGESTED CODE CHANGE (not applied — refresh never edits scripts):
  `scripts/ora_score.py` → `API`, `GRADE_SCALE`, `summarize()` still assume the
  old five-layer envelope. Layer breakdown output will be wrong or empty until
  updated. Needs user approval.

**Cloudflare access policy (PRIMARY: developers.cloudflare.com changelog
2026-07-01 + blog)**
- Corrected an over-broad claim. The 2026-09-15 defaults apply to **new domains
  only** and block Training/Agent **on ad-displaying pages**, not outright, and
  not "for new/free zones" generally. Search stays allowed everywhere.
- Search/Agent/Training controls are available to all plans incl. Free today;
  existing customers may opt out before 2026-09-15.
- Added "Redirects for AI Training" (canonical-content enforcement).

**AI crawler roster (PRIMARY: developers.openai.com/api/docs/bots,
support.claude.com/en/articles/8896518)**
- No new or renamed bots. OpenAI bot versions now 1.4 (was 1.2).
- Anthropic IP ranges confirmed published at `https://claude.com/crawling/bots.json`
  (single file covering ClaudeBot, Claude-User, Claude-SearchBot); Crawl-delay
  supported. Anthropic doc lists no retired tokens — `anthropic-ai` / `claude-web`
  retained as historical stale-token flags.

**Structured data (PRIMARY: developers.google.com search-gallery + updates)**
- FAQ: added that **Search Console API support was removed August 2026**;
  Google says existing FAQPage markup need not be removed.
- Added **Practice Problems** to the deprecated list (Search Console reporting,
  Rich Results Test and appearance filter removed January 2026).
- ⚠️ SUGGESTED CODE CHANGE: `scripts/schema_extract.py` →
  `DEPRECATED_RICH_RESULTS` should gain a Practice Problems entry.
- *Unconfirmed, monitoring*: Search Engine Land reports Google removing
  "nutrition facts" and "nearby offers" features. No primary Google source
  found — NOT ingested.

**Agent readiness (PRIMARY: developer.chrome.com)**
- Lighthouse Agentic Browsing requires **Chrome 150+**; Google labels the
  category **informational and unbenchmarked** — recorded so reports stop
  presenting it as a graded number.
- WebMCP origin trial opens in **Chrome 149**; also available via
  `chrome://flags/#enable-webmcp-testing`. Gemini in Chrome to consume WebMCP.

**Unchanged / re-verified**: Core Web Vitals thresholds (LCP 2.5s / INP 200ms /
CLS 0.1), llms.txt status, IndexNow (Google still absent), Google AI-features
guidance. Google's July-Aug 2026 doc updates contained nothing affecting this
skill's checks (Product `category` property, incentivized-review guideline,
preferred-sources button).

## 2026-10-18 — refresh
- WebMCP: origin trial range set to Chrome 149–156 (PRIMARY: blink-dev "Intent to Experiment: WebMCP", approved 2026-05-18, https://groups.google.com/a/chromium.org/g/blink-dev/c/gmYffo5WOE8).
- Unconfirmed, monitoring (SECONDARY only): new crawler tokens Reflectionbot, GrokAgent, meta-externaltest, ZipchatBot (technologychecker.io, Oct 2026); WebMCP moving navigator.modelContext → document.modelContext in Chrome 150 (one guide, Aug 2026).
- No new Google structured-data deprecations or AI-feature guidance changes found for Sept–Oct 2026; Core Web Vitals unchanged.

## 2026-11-08 — refresh
- WebMCP: Chrome's Imperative API page (PRIMARY, https://developer.chrome.com/docs/ai/webmcp/imperative-api, updated 2026-10-16) registers tools on `document.modelContext.registerTool()`; `navigator.modelContext` is the legacy fallback. Confirms the item monitored on 2026-10-18.
- Structured data: no new Google deprecations found after FAQ (May 2026) and Practice Problems (Jan 2026).
- Crawlers: no vendor announcements from OpenAI, Anthropic or Perplexity for Oct–Nov 2026. Secondary only, monitoring: Cloudflare directory reportedly at 95 AI bots.
