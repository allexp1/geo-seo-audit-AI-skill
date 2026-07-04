# Local SEO

For businesses with physical presence (retail, services, clinics, studios, restaurants, agencies with offices) or service-area-specific reach (plumbers, photographers, local trainers). Local SEO is the difference between showing up in the "3-pack" map result and being invisible to 70% of nearby searchers.

## The three pillars

1. **Google Business Profile (GBP)** — the single most important local-SEO asset
2. **Citations + NAP consistency** — name, address, phone across the web
3. **Reviews + review-response** — velocity, volume, variety

Technical SEO and content still matter, but these three dominate local rankings.

## Google Business Profile — setup and optimization

### Claim and verify

```
1. Go to business.google.com
2. Claim the listing (or create one)
3. Verify via postcard, phone, email, video (varies by category)
4. Complete 100% of profile fields — yes, all of them
```

### Fields that matter most

| Field | Impact | Notes |
|-------|--------|-------|
| Primary category | High | Pick the most specific that fits; affects ranking eligibility |
| Secondary categories | High | Up to 9; don't bloat — stay relevant |
| Business name | Critical | Legal name only; no keyword stuffing (violates GBP policy) |
| Address | Critical | Must match website, citations, and license exactly |
| Service area | Medium | For service-area businesses, list actual cities/ZIPs served |
| Website URL | High | Use UTM params for tracking: `?utm_source=gbp` |
| Phone | Critical | Local number beats toll-free for ranking |
| Hours | Medium | Keep accurate; special hours for holidays |
| Photos | Medium-High | 20+ photos, weekly updates signal activity |
| Products/Services | Medium | List specific offerings with prices when possible |
| Attributes | Low-Medium | Wheelchair accessible, Wi-Fi, LGBTQ-friendly, etc. |
| Q&A | Low-Medium | Seed 5-10 common questions with owner-authored answers |
| Posts | Low-Medium | Weekly posts (announcements, offers, events) |

### Policy-safe naming

```
❌ "Dr. Smith Dentist Best in Chicago Teeth Whitening Dental Implants"
   Will get suspended.

✅ "Smith Family Dental"
   + Primary category: Dentist
   + Secondary: Cosmetic dentist, Dental implants provider
```

## NAP consistency and citations

**NAP** = Name, Address, Phone. Must be identical across:
- Your website (structured data + visible content)
- GBP
- Apple Maps, Bing Places
- Yelp, Yellowpages, BBB
- Industry-specific directories (Avvo, Healthgrades, Houzz, etc.)
- Chamber of Commerce, local business associations

**Citation builders:** BrightLocal, Whitespark, Moz Local, Yext. Or do it manually for 30–50 citations — more effective but labor-intensive.

**The real "why":** Google triangulates business legitimacy from NAP consistency across the web. A business with 50 identical NAPs across 50 sources beats a business with 10 inconsistent NAPs.

## Reviews — the ranking lever nobody wants to do

Review signals Google measures:
- **Volume** — total review count
- **Velocity** — reviews per month, consistent over time
- **Rating** — average (aim >4.5)
- **Variety** — reviews across platforms (GBP, Yelp, Facebook, industry-specific)
- **Keyword density** — reviews mentioning services / locations naturally
- **Responses** — owner-response rate (aim 100%)
- **Recency** — recent reviews weighted more

### Review-generation playbook

1. Automate ask: every completed job / appointment → SMS or email with direct GBP review link
2. Make the link one-click: `https://search.google.com/local/writereview?placeid=YOUR_PLACE_ID`
3. Respond within 24 hours to every review (positive AND negative)
4. Address negative reviews factually — never defensively. Invite private follow-up.
5. Never incentivize — Google policy violation, and fake reviews get scrubbed

### Review response templates

**Positive (5⭐):**
> "Thank you, {name} — {specific-thing-they-mentioned} is exactly what we aim for. We appreciate you taking the time, and we look forward to seeing you again."

**Negative (1–2⭐):**
> "Hi {name}, I'm sorry your experience didn't meet expectations. {Acknowledge the specific issue without being defensive}. I'd like to make this right — please reach me directly at {email} or {phone} so I can address it personally."

## LocalBusiness schema

Add to every page (homepage priority). Schema.org has specific subtypes — use the most specific (e.g., `Dentist`, `HairSalon`, `Restaurant`, `LegalService`) instead of generic `LocalBusiness`.

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Dentist",
  "@id": "https://example-dental.com/#business",
  "name": "Smith Family Dental",
  "image": [
    "https://example-dental.com/photos/exterior.jpg",
    "https://example-dental.com/photos/reception.jpg",
    "https://example-dental.com/photos/operatory.jpg"
  ],
  "url": "https://example-dental.com",
  "telephone": "+1-312-555-0100",
  "priceRange": "$$",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "123 Main Street, Suite 400",
    "addressLocality": "Chicago",
    "addressRegion": "IL",
    "postalCode": "60601",
    "addressCountry": "US"
  },
  "geo": {
    "@type": "GeoCoordinates",
    "latitude": 41.8819,
    "longitude": -87.6278
  },
  "openingHoursSpecification": [
    {
      "@type": "OpeningHoursSpecification",
      "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
      "opens": "08:00",
      "closes": "17:00"
    },
    {
      "@type": "OpeningHoursSpecification",
      "dayOfWeek": "Saturday",
      "opens": "09:00",
      "closes": "13:00"
    }
  ],
  "sameAs": [
    "https://www.facebook.com/smithfamilydental",
    "https://www.instagram.com/smithfamilydental",
    "https://www.yelp.com/biz/smith-family-dental-chicago",
    "https://g.page/smithfamilydental"
  ],
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.8",
    "reviewCount": "247"
  }
}
</script>
```

### Multi-location businesses

For chains / franchises, publish one `LocalBusiness` per physical location, each at its own URL (`/locations/chicago`, `/locations/austin`). Link between them via `parentOrganization`.

## Service pages — local landing pages

```
example-dental.com/
├── services/
│   ├── teeth-whitening/          ← homepage for the service
│   ├── teeth-whitening-chicago/  ← city-specific landing
│   └── teeth-whitening-austin/   ← another city
```

Avoid "doorway pages" — each should have unique content (local testimonials, local case studies, directions from nearby landmarks, local pricing, neighborhood-specific photos). Programmatic templates that fill in only the city name get flagged as spam.

## Maps Pack / 3-Pack ranking factors (2026)

Ordered roughly by weight:

1. Primary category + GBP completeness
2. Proximity to searcher (can't control, except by having multiple locations)
3. Review signals (volume, velocity, rating, responses)
4. NAP consistency + citation authority
5. Links to the GBP landing page (LocalBusiness schema + backlinks)
6. Behavioral signals (click-through, direction requests, calls from GBP)
7. Content relevance (service pages, city-specific pages)

## Audit workflow

```bash
# 1. GBP completeness — log into business.google.com, score each field
# 2. NAP audit — search for your business name; note any inconsistent listings
curl -s "https://www.google.com/search?q=%22Smith+Family+Dental%22+Chicago" | grep -oE '<a[^>]+href="[^"]+"[^>]*>[^<]{5,}' | head -30

# 3. Citation audit — use free tools
# Moz Local: https://moz.com/local/search
# BrightLocal: https://www.brightlocal.com/local-seo-tools/local-citation-finder/

# 4. Review audit — GBP, Yelp, industry-specific
# 5. Schema validation
# https://search.google.com/test/rich-results

# 6. Competitor analysis — Google search from target city, note 3-pack results
```

## Common pitfalls

- Business name with keyword stuffing → GBP suspension
- Multiple inconsistent addresses across citations → low rank
- Using a virtual office for a service-area business → GBP removal
- Ignoring negative reviews → social proof erodes
- No LocalBusiness schema → leaves trust signal on the table
- Service-area businesses that don't hide the address → reduces trust
- City landing pages with duplicate content → thin-content penalty
- No phone number on GBP (only email) → call-from-GBP ranking signal goes unused

## Local SEO audit checklist

### Foundation
- [ ] GBP claimed, verified, 100% complete
- [ ] Primary category specific + 3-5 secondary categories
- [ ] NAP consistent across GBP, website, top 10 citations
- [ ] 30+ citations on relevant directories
- [ ] LocalBusiness schema on homepage and location pages

### Reviews
- [ ] 25+ GBP reviews
- [ ] 4.5+ average rating
- [ ] Reviews received in last 30 days
- [ ] 100% owner response rate
- [ ] Reviews on at least 2 non-GBP platforms (Yelp + industry-specific)

### Content
- [ ] Homepage targets "[service] in [city]"
- [ ] Dedicated page per service
- [ ] Dedicated landing per city (if multi-location or service-area)
- [ ] City content is unique (not templated duplicates)
- [ ] Directions / neighborhood context on location pages

### Engagement
- [ ] Weekly GBP posts
- [ ] 20+ GBP photos, updated monthly
- [ ] Q&A seeded with 5-10 common questions
- [ ] Events / offers posted when relevant

## When local SEO doesn't apply

Pure online / digital products (SaaS, mobile apps, e-commerce without physical retail) should skip this entirely. Don't fake a "location" for local SEO — it's a policy violation and doesn't work anyway.
