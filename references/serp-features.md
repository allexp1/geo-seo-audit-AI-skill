# SERP Features — Targeting Beyond Blue Links

Modern Google SERPs contain ~15 different features beyond the classic 10 blue links. Many intercept clicks before the organic results. Winning in SERPs in 2026 = winning SERP features, not just positions.

## The features, ranked by strategic value

### 1. AI Overview / Search Generative Experience (SGE)

**What:** AI-generated summary at top of SERP, with cited sources.
**Click impact:** Depends on query — 30–70% click intercept on informational queries.
**How to win a citation:**
- 40-60 word direct-answer paragraphs
- `FAQPage` + `Article` schema
- Authoritative source signals (E-E-A-T, `sameAs`, author bios)
- Recently updated content (`dateModified`)
- Cross-linked with knowledge-graph entities (Wikidata, LinkedIn)
- See `references/ai-visibility-testing.md` to measure citation rate

**AEO wins over SEO here:** don't optimize for rank, optimize for citation.

### 2. Featured Snippet (classic, pre-AIO)

**What:** Bold-boxed answer at position 0.
**Click impact:** 20–40% CTR on the featured URL (often higher than position 1).
**How to win:**

```html
<!-- Paragraph snippet -->
<h2>What is SIP trunking?</h2>
<p>SIP trunking is a method of delivering voice calls over the internet
using the Session Initiation Protocol (SIP). It replaces traditional
physical phone lines with virtual channels, typically saving businesses
25-65% compared to ISDN PRI lines.</p>

<!-- List snippet -->
<h2>How to pick a SIP trunking provider</h2>
<ol>
  <li>Check regulatory licensing in your operating countries</li>
  <li>Confirm 99.99%+ uptime SLA with measurable credits</li>
  <li>Verify DID number availability in your markets</li>
  <li>Test voice quality with a trial</li>
  <li>Review KYC / STIR-SHAKEN / AML compliance</li>
</ol>

<!-- Table snippet -->
<h2>SIP trunking providers compared</h2>
<table>
  <thead><tr><th>Provider</th><th>Countries</th><th>Starting price</th></tr></thead>
  <tbody>...</tbody>
</table>
```

**Rules:**
- H2 / H3 matches the question exactly
- Answer is 40–60 words (paragraph) or 5–8 items (list)
- Content is self-contained — no "as mentioned above"
- Place answer within first 300 words of page

### 3. People Also Ask (PAA)

**What:** Expandable Q&A accordion, usually position 2–4 on SERP.
**Click impact:** 15–25% CTR when a PAA question matches intent.
**How to win:**
- Include 5-10 related questions as H2/H3 on your page
- Use exact question phrasing (match how users ask)
- Answer each in 40-60 words
- Add `FAQPage` schema
- Sources: Google Autocomplete, AlsoAsked.com, AnswerThePublic

PAA is a citation bonanza for AEO — if you win a PAA slot, you often also win the AI Overview citation.

### 4. Image Pack

**What:** Horizontal row of images, linking to Google Images.
**Click impact:** High for visual-intent queries; low for text-intent.
**How to win:**
- Descriptive filenames (`blue-widget-side-view.webp`, not `IMG_12345.jpg`)
- Alt text describing the visible content specifically
- High-resolution (≥1200px wide)
- `ImageObject` schema with caption, description, creator, copyrightHolder
- Context — image appears on a page with related text
- Unique, not stock (Google demotes duplicate stock images)

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "ImageObject",
  "contentUrl": "https://example.com/images/dental-operatory-chicago.jpg",
  "caption": "Operatory at Smith Family Dental, Chicago",
  "description": "Modern dental operatory with intraoral camera and digital radiography",
  "creator": { "@type": "Organization", "name": "Smith Family Dental" },
  "copyrightNotice": "© 2026 Smith Family Dental",
  "license": "https://example.com/image-license",
  "acquireLicensePage": "https://example.com/licenses"
}
</script>
```

### 5. Video Pack / YouTube

**What:** Horizontal row of video thumbnails.
**Click impact:** High for how-to / comparison / review queries.
**How to win:**
- YouTube dominates; owning on-site video is secondary
- If you publish video, add `VideoObject` schema
- Transcript on page (searchable + accessible)
- Title + description + tags optimized for the query
- Suggested chapters with timestamps

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "VideoObject",
  "name": "How to pick a SIP trunking provider in 2026",
  "description": "A 5-minute framework for evaluating global DID carriers.",
  "thumbnailUrl": "https://example.com/video-thumb.jpg",
  "uploadDate": "2026-03-15",
  "duration": "PT5M12S",
  "contentUrl": "https://example.com/videos/pick-sip-provider.mp4",
  "embedUrl": "https://www.youtube.com/embed/abc123"
}
</script>
```

### 6. Local Pack / Map 3-Pack

See `references/local-seo.md` — entirely separate optimization stack.

### 7. Sitelinks

**What:** Up to 6 linked sub-pages beneath the main result, typically for branded queries.
**Click impact:** Expands real estate 3-5×; claims more of the SERP.
**How to win:**
- Clean navigation hierarchy
- Descriptive page titles
- Strong internal linking from homepage to key sub-pages
- Don't try to manually configure — Google auto-selects based on site structure

### 8. Review Stars (Rich Result)

**What:** Gold stars + rating number beneath the result.
**Click impact:** 20–30% CTR lift.
**How to win:**
- `Review` or `AggregateRating` schema on product / service / recipe / course / event pages
- Must reflect genuine reviews (fake reviews get manual penalties)
- Visible reviews on the page itself — not just in schema

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "FitBeat Music",
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.7",
    "reviewCount": "183",
    "bestRating": "5",
    "worstRating": "1"
  }
}
</script>
```

### 9. Knowledge Panel

See `references/knowledge-graph.md`.

### 10. Shopping / Product results

**What:** Horizontal product carousel with images, prices, merchants.
**Click impact:** Very high for transactional queries.
**How to win:**
- `Product` + `Offer` schema with price, availability, shipping
- Google Merchant Center feed
- GTIN / MPN / SKU where applicable
- Fresh pricing (stale prices = removed from shopping)

### 11. Events

**What:** Event cards for venues / concerts / conferences.
**How to win:** `Event` schema with date, location, ticket URL.

### 12. Recipes

**What:** Recipe cards with image, rating, cook time.
**How to win:** `Recipe` schema with ingredients, instructions, nutrition, ratings.

### 13. Jobs

**What:** Google for Jobs listings (above organic on job queries).
**How to win:** `JobPosting` schema with salary, location, description, datePosted.

### 14. FAQ / How-To rich results

**What:** Expandable Q&A or step list beneath the blue link.
**Click impact:** Reduced slightly in 2023 Google update, still visible.
**How to win:** `FAQPage` / `HowTo` schema.

Note: Google reduced FAQ rich result display in 2023, limiting it to authoritative sites. Still valuable for AEO citation.

### 15. Twitter / X Cards

**What:** Recent tweets embedded in SERP for trending / branded queries.
**How to win:** Active, verified X presence + posting on-topic content.

## Tracking what you win

Google Search Console exposes Rich Results in the "Enhancements" section:
- FAQ
- HowTo
- Product snippets
- Breadcrumb
- Logo
- Events
- Video
- Review
- Job postings
- Recipe

Monitor valid / warning / error counts weekly.

## What's losing ground in 2026

- **FAQ rich results** — Google deprioritized in 2023; still useful for AEO but not for SERP CTR
- **HowTo rich results** — same story
- **Featured snippets** — being absorbed into AI Overviews; direct snippet CTR declining
- **Organic blue links** — shrinking slice of the SERP overall

## What's rising

- **AI Overview citations** — the future of search visibility
- **Image / Video packs** — visual intent queries growing
- **Local Pack** — still dominant for geo queries
- **Knowledge Panel** — brand-defining real estate

## Audit checklist

- [ ] Identify top 20 queries you rank for (GSC data)
- [ ] For each, note which SERP features appear (AIO, featured snippet, PAA, image pack, etc.)
- [ ] For features you don't own, identify specific optimization steps
- [ ] Implement schema for every relevant SERP feature
- [ ] Track Rich Results valid count in GSC Enhancements
- [ ] Measure AI Overview citation rate monthly (via `scripts/ai-citation-test.mjs`)
