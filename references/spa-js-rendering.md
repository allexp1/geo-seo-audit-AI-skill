# SPA / JavaScript Rendering for SEO

Single-page applications (React, Vue, Angular, Svelte) can rank as well as server-rendered sites — if done right. Most don't. The difference between a correctly-rendered SPA and an SEO-broken one is often the difference between 100,000 organic visits/month and 1,000.

## The core problem

Googlebot renders JavaScript. Other search bots mostly don't. AI crawlers (GPTBot, ClaudeBot, PerplexityBot) variably do. Result:

- Googlebot may eventually see your full SPA (after a render queue delay of seconds to days)
- Bing, Yandex, AI crawlers may see only the initial HTML
- If your initial HTML is `<div id="root"></div>` with nothing else, you're invisible to all non-Googlebot crawlers

## Rendering strategies — the 4 options

### 1. Client-Side Rendering (CSR) — AVOID for SEO pages

```
Request → Server returns empty HTML shell → Browser runs JS → Content appears
```

- Fast deploys
- Simple infrastructure
- **Terrible for SEO / AEO** — non-Googlebot crawlers see empty HTML
- Googlebot sees content but with multi-day render delays

Use for: private/authenticated pages behind login. Not SEO pages.

### 2. Server-Side Rendering (SSR) — BEST for dynamic content

```
Request → Server fetches data + renders HTML → Browser hydrates → Interactive
```

- Full HTML on first response
- All crawlers see content
- Fresh data on every request
- Higher server costs
- Slower TTFB (time to first byte) than static

Use for: user-personalized content, frequently-changing data, search results, filtered listings.

**Frameworks:** Next.js (SSR mode), Remix, Nuxt.js, SvelteKit, Astro (SSR adapter)

### 3. Static Site Generation (SSG) — BEST for mostly-static pages

```
Build time: Page rendered to HTML → Stored as static file
Request: Serve static HTML directly from CDN edge
```

- Fastest possible TTFB
- Every crawler sees full HTML
- Cheap to host (static files)
- Requires rebuild on content change (minutes at scale)

Use for: blog posts, documentation, marketing pages, anything that changes daily or less.

**Frameworks:** Next.js (SSG), Gatsby, Astro (default), Eleventy, Hugo, Jekyll

### 4. Incremental Static Regeneration (ISR) — BEST for large programmatic sites

```
First request: generate + cache at edge
Subsequent: serve cached until TTL expires
Expires: regenerate in background, serve stale while rebuilding
```

- Static performance + dynamic flexibility
- Great for 10K+ programmatic pages
- Per-page TTL configurable

Use for: Zillow-style listings, e-commerce catalogs, anything where "mostly fresh is fine."

**Frameworks:** Next.js (`revalidate`), Vercel Cache Components, Astro on Vercel

## The decision matrix

| Page type | Recommended |
|-----------|-------------|
| Marketing homepage | SSG |
| Blog posts | SSG |
| Documentation | SSG |
| Product listings (small) | SSG |
| Product listings (10K+) | ISR |
| Product detail | SSR or ISR |
| Search results | SSR |
| Filter / sort pages | SSR |
| User dashboard | CSR (behind auth) |
| Checkout flow | SSR or CSR |

## Auditing your SPA

### View source vs. view rendered — the fundamental test

```bash
# What crawlers see (raw HTML from server)
curl -s https://yoursite.com/page | grep -E "<h1|<p|<a|<li" | head -20

# What users see (JS-rendered)
# Open Chrome DevTools → Elements tab → copy outer HTML
```

If curl returns an empty shell but DevTools shows content, non-Googlebot crawlers are blind.

### Test Googlebot specifically

```bash
curl -s -A "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)" \
  https://yoursite.com/page | grep -E "<h1|<p" | head -20
```

Some sites send different HTML to Googlebot user agent. Not recommended (Google considers consistency a quality signal) but worth knowing.

### Mobile-first check

Googlebot-Mobile is the primary crawler. Audit in Chrome's mobile device emulation AND via curl with mobile UA:

```bash
curl -s -A "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 Googlebot/2.1" \
  https://yoursite.com | grep -c "<h1"
```

### Google Search Console — URL Inspection

1. Inspect any URL
2. Click "View crawled page"
3. See the HTML Google actually fetched + the rendered screenshot
4. Compare what's there vs. what's in your DevTools

Discrepancies = rendering problems.

## Common SPA SEO failures

### 1. Client-side routing breaks indexing

```javascript
// ❌ Pure JS navigation — search bots miss state changes
function handleClick() {
  history.pushState({}, '', '/new-page');
  renderNewPageContent();
}
```

Use real `<a href>` tags with proper URLs. Let the framework handle the route (React Router, Next.js Link, etc.) but make sure server responses to those URLs are valid HTML.

### 2. Hash routing (`#`) — completely invisible to crawlers

```
❌ https://example.com/#/products/123
```

Google ignores everything after `#`. Use path-based routing:

```
✅ https://example.com/products/123
```

### 3. Canonical URLs set client-side only

```javascript
// ❌ Set after hydration — invisible to non-JS crawlers
useEffect(() => {
  document.querySelector('link[rel=canonical]').href = currentUrl;
}, []);
```

Canonical tags must be in the initial HTML response. Set them server-side (SSR) or at build time (SSG).

### 4. Meta tags rendered only client-side

Same as canonical — `<title>`, `<meta description>`, OG tags must be in the server response, not swapped in by JS after mount.

Framework solutions:
- Next.js: `metadata` export in App Router, `Head` component in Pages Router
- Remix: `meta` export
- Nuxt: `useHead` composable
- SvelteKit: `<svelte:head>`

### 5. Lazy-loaded content above the fold

Important content (the H1, first paragraph, main imagery) loaded via JS fetch after mount → invisible to many crawlers, slow for Core Web Vitals.

Rule: content critical to understanding the page must be in the initial HTML. Lazy-load only below-the-fold, non-core content.

### 6. JSON-LD schema injected via JS

```javascript
// ❌ Injected after hydration
useEffect(() => {
  const script = document.createElement('script');
  script.type = 'application/ld+json';
  script.text = JSON.stringify(schema);
  document.head.appendChild(script);
}, []);
```

Must be in initial HTML. Use framework-native schema injection:

```jsx
// ✅ Next.js App Router
export const metadata = { ... };
// Or inline:
<script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }} />
```

### 7. Infinite scroll without pagination URLs

User scrolls, more items load, URL never changes. Crawler can't reach item 50 on page. Bad.

Fix: implement pagination URLs as backup (`/products?page=2`) with real content at those URLs. The infinite scroll is UX on top; the underlying URLs let crawlers reach everything.

### 8. Service worker caching serves stale HTML to bots

Aggressive service worker strategies can serve cached HTML to Googlebot that predates recent content updates. Validate with "URL Inspection → View crawled page."

### 9. Noindex tag set dynamically

```javascript
// Setting noindex based on route state can race against crawl
if (isLoginPage) setMeta('robots', 'noindex');
```

Prefer server-side noindex via HTTP header (`X-Robots-Tag: noindex`) or initial HTML meta tag.

### 10. CSR-only error pages

If your 404/500 pages require JS to render the "Not Found" content, the page may return 200 + empty to crawlers. Confirm status codes with:

```bash
curl -I https://yoursite.com/nonexistent-page
# Should return: HTTP/2 404
```

Soft 404s (200 status + "not found" content) are a common SPA pitfall.

## Performance implications

SPAs often fail Core Web Vitals even when rendering correctly:

- **LCP** (Largest Contentful Paint) — SSR helps; CSR typically 1-3 seconds worse
- **CLS** (Cumulative Layout Shift) — hydration mismatches cause visible shifts
- **INP** (Interaction to Next Paint) — JS heavy SPAs struggle here
- **FCP** (First Contentful Paint) — SSR >> CSR

Google uses Core Web Vitals as a ranking factor (page experience). Slow SPA = slower rankings.

## AEO implications

AI crawlers (GPTBot, ClaudeBot, PerplexityBot) in 2026 have uneven JS rendering support. Safe posture:

- Critical content in initial HTML
- `<llms.txt>` with clean markdown links (bypasses JS entirely — see `references/llms-txt-guide.md`)
- Pre-rendered `.md` versions of key pages at clean URLs
- Schema.org markup in HTML (not JS-injected)

The bot doesn't have to render your SPA if you give it a flat markdown alternative.

## Audit checklist

- [ ] Run `curl -s https://yoursite.com/ | wc -c` — initial HTML ≥ 5KB of real content for each template
- [ ] `curl` returns the `<h1>` visible in the browser
- [ ] `curl` returns `<meta name="description">` populated
- [ ] `curl` returns JSON-LD schema blocks
- [ ] `curl` with mobile UA returns same content as desktop
- [ ] Google Search Console → URL Inspection shows "Page is indexed" with rendered preview matching browser view
- [ ] Canonical URL in initial HTML (not JS-set)
- [ ] Routes produce real status codes (200/301/404) not soft 404s
- [ ] Rendering strategy documented per page type (SSG vs SSR vs ISR vs CSR)
- [ ] Core Web Vitals pass on mobile
- [ ] No JS errors on initial load (check console)
- [ ] If CSR used, audited for non-SEO pages only
