# Trusted sources for the Refresh Protocol

Consulted when refreshing KNOWLEDGE.md. PRIMARY findings apply directly;
SECONDARY findings need confirmation from a PRIMARY source first.

**Review this file manually once** — it is the weakest link: if a source here
is wrong or goes stale, refreshes ingest junk. The refresh process itself
never modifies this file.

## PRIMARY — official docs, specs, changelogs

- https://developers.openai.com/api/docs/bots — OpenAI crawler UAs (GPTBot, OAI-SearchBot, ChatGPT-User, OAI-AdsBot); new/renamed bots
- https://support.claude.com/en/articles/8896518 (or current Anthropic crawler doc) — ClaudeBot / Claude-SearchBot / Claude-User tokens
- https://docs.perplexity.ai/guides/bots — PerplexityBot / Perplexity-User
- https://developers.google.com/search/docs/crawling-indexing/overview-google-crawlers — Google crawler tokens (Google-Extended, Google-CloudVertexBot, etc.)
- https://developers.google.com/search/docs/fundamentals/ai-optimization-guide — Google's official AI Overviews / AI Mode guidance
- https://developers.google.com/search/docs/appearance/structured-data/search-gallery — supported structured data types; deprecation notices
- https://status.search.google.com/products/rGHU1u87FJnkP6W2GwMi/history — Google core/spam update history
- https://web.dev/articles/vitals + https://developer.chrome.com/docs/crux/release-notes — Core Web Vitals metrics and thresholds
- https://developer.chrome.com/docs/lighthouse/agentic-browsing/scoring — Lighthouse Agentic Browsing checks
- https://developer.chrome.com/docs/ai/webmcp — WebMCP status, origin trial, API shape
- https://blog.cloudflare.com/ (tags: ai-crawl-control, bots) + https://developers.cloudflare.com/ai-crawl-control/ — default AI blocking, Content Signals, Pay Per Use, Web Bot Auth, BotBase
- https://llmstxt.org — llms.txt spec changes
- https://ora.ai/docs + https://ora.ai/api/openapi.json + https://ora.ai/methodology — ora.ai API endpoints, rate limits, layers, grade scale
- https://github.com/nlweb-ai/NLWeb (or current NLWeb repo) — NLWeb endpoints and MCP behavior
- https://www.indexnow.org/searchengines — IndexNow engine support (watch for Google joining)
- https://schema.org/docs/releases.html — schema.org vocabulary releases
- https://github.com/agentic-commerce-protocol/agentic-commerce-protocol — ACP spec changes

## SECONDARY — hints, must be confirmed by a PRIMARY source

- Search topic: "new AI crawler user agent robots.txt <current year>" — early word of new bots
- Search topic: "Google AI Overviews citation study" — citation-correlation numbers (44%-in-first-30% style stats)
- https://www.searchenginejournal.com + https://searchengineland.com — deprecations, algorithm updates, feature launches
- https://ahrefs.com/blog + https://www.semrush.com/blog — large-scale correlation studies
- Search topic: "llms.txt adoption study" — adoption/consensus shifts
- Search topic: "agent readiness score website checklist" — new industry checkable dimensions
- Search topic: "GEO tools AI visibility scoring dimensions" — what Profound/Otterly/Peec/HubSpot measure

## Known junk patterns (do not ingest)

- Claims of new Core Web Vitals thresholds or metrics not present on web.dev /
  CrUX release notes (recurring content-farm fabrication, e.g. "LCP 2.0s",
  "Engagement Reliability").
- "Google now reads llms.txt" claims without a google.com source.
