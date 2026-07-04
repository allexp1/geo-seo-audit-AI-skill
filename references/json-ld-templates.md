# JSON-LD Templates — Schema.org

Copy-paste starting points for the most impactful schema types. Validate every implementation at [Google Rich Results Test](https://search.google.com/test/rich-results) and [Schema.org Validator](https://validator.schema.org/).

**Rule of thumb:** every schema property must reflect visible page content. Hidden or fabricated schema triggers manual penalties.

## Table of contents

- [Organization](#organization) — every homepage
- [WebSite](#website) — every homepage
- [LocalBusiness](#localbusiness) — physical locations (use specific subtype)
- [Person](#person) — author bio pages
- [Article / NewsArticle / BlogPosting](#article) — editorial content
- [FAQPage](#faqpage) — FAQ sections
- [HowTo](#howto) — step-by-step guides
- [Product](#product) — e-commerce or product pages
- [Review / AggregateRating](#review) — reviews
- [Recipe](#recipe) — food content
- [Event](#event) — events, conferences, webinars
- [Course](#course) — educational programs
- [VideoObject](#videoobject) — video content
- [SoftwareApplication / MobileApplication](#softwareapplication) — apps
- [Service](#service) — service offerings
- [JobPosting](#jobposting) — career listings
- [BreadcrumbList](#breadcrumblist) — site hierarchy navigation
- [Dataset](#dataset) — data products / research
- [Book](#book) — published books
- [Offer / AggregateOffer](#offer) — pricing
- [SearchAction](#searchaction) — sitelinks search box

---

## Organization

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "@id": "https://example.com/#organization",
  "name": "Example Corp",
  "legalName": "Example Corporation, Inc.",
  "url": "https://example.com",
  "logo": {
    "@type": "ImageObject",
    "url": "https://example.com/logo.png",
    "width": 600,
    "height": 60
  },
  "description": "Platform for X that helps Y do Z.",
  "foundingDate": "2020-03-15",
  "founders": [
    { "@type": "Person", "name": "Jane Smith", "url": "https://example.com/team/jane" }
  ],
  "numberOfEmployees": { "@type": "QuantitativeValue", "value": 45 },
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "123 Main Street",
    "addressLocality": "San Francisco",
    "addressRegion": "CA",
    "postalCode": "94105",
    "addressCountry": "US"
  },
  "contactPoint": [{
    "@type": "ContactPoint",
    "telephone": "+1-415-555-0100",
    "contactType": "customer service",
    "email": "support@example.com",
    "availableLanguage": ["English", "Spanish"]
  }],
  "sameAs": [
    "https://en.wikipedia.org/wiki/Example_Corp",
    "https://www.wikidata.org/wiki/Q12345",
    "https://www.crunchbase.com/organization/example-corp",
    "https://www.linkedin.com/company/example-corp",
    "https://twitter.com/examplecorp",
    "https://github.com/examplecorp"
  ]
}
</script>
```

## WebSite

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "@id": "https://example.com/#website",
  "url": "https://example.com",
  "name": "Example",
  "publisher": { "@id": "https://example.com/#organization" },
  "inLanguage": "en-US",
  "potentialAction": {
    "@type": "SearchAction",
    "target": {
      "@type": "EntryPoint",
      "urlTemplate": "https://example.com/search?q={search_term_string}"
    },
    "query-input": "required name=search_term_string"
  }
}
</script>
```

## LocalBusiness

Use the most specific subtype from [schema.org/LocalBusiness](https://schema.org/LocalBusiness) — `Dentist`, `Restaurant`, `HairSalon`, `LegalService`, `MedicalBusiness`, etc.

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
    }
  ],
  "sameAs": [
    "https://www.facebook.com/smithfamilydental",
    "https://www.yelp.com/biz/smith-family-dental-chicago"
  ],
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.8",
    "reviewCount": "247"
  }
}
</script>
```

## Person

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Person",
  "@id": "https://example.com/authors/jane-smith#person",
  "name": "Jane Smith",
  "image": "https://example.com/jane-smith.jpg",
  "jobTitle": "Senior Voice Infrastructure Analyst",
  "worksFor": {
    "@type": "Organization",
    "name": "Example Voice Research"
  },
  "alumniOf": [
    { "@type": "EducationalOrganization", "name": "Massachusetts Institute of Technology" }
  ],
  "knowsAbout": ["SIP trunking", "Voice infrastructure", "CPaaS", "Voice AI"],
  "sameAs": [
    "https://en.wikipedia.org/wiki/Jane_Smith_(analyst)",
    "https://www.wikidata.org/wiki/Q98765",
    "https://linkedin.com/in/janesmith",
    "https://twitter.com/janesmithvoice",
    "https://github.com/janesmith",
    "https://scholar.google.com/citations?user=xxxxxxx"
  ],
  "url": "https://example.com/authors/jane-smith"
}
</script>
```

## Article

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "mainEntityOfPage": {
    "@type": "WebPage",
    "@id": "https://example.com/guides/sip-trunk-pick"
  },
  "headline": "How to pick a SIP trunking provider in 2026",
  "description": "A 6-criteria framework for choosing a global DID carrier.",
  "image": [
    "https://example.com/article-hero.jpg"
  ],
  "author": {
    "@type": "Person",
    "@id": "https://example.com/authors/jane-smith#person"
  },
  "publisher": {
    "@type": "Organization",
    "@id": "https://example.com/#organization"
  },
  "datePublished": "2026-03-15T10:00:00+00:00",
  "dateModified": "2026-04-18T14:30:00+00:00",
  "articleSection": "SIP Trunking",
  "keywords": ["SIP trunking", "DID carrier", "voice infrastructure"],
  "wordCount": 2150,
  "inLanguage": "en-US"
}
</script>
```

For news: `@type: "NewsArticle"`. For blog posts: `@type: "BlogPosting"`. Same structure.

## FAQPage

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "What is SIP trunking?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "SIP trunking is a method of delivering voice calls over the internet using the Session Initiation Protocol. It replaces traditional physical phone lines with virtual channels, typically saving businesses 25–65% compared to ISDN PRI lines."
      }
    },
    {
      "@type": "Question",
      "name": "How much does SIP trunking cost in 2026?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Per-minute rates range from $0.0035 inbound to $0.005 outbound for US calls (e.g., Telnyx). Per-channel pricing runs $8–25 per month. Enterprise deals are typically custom. Expect $50–500 per month total for small businesses."
      }
    }
  ]
}
</script>
```

Answer length: 40-60 words ideal for AEO extraction.

## HowTo

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "HowTo",
  "name": "How to set up a SIP trunk with a voice AI agent",
  "description": "Configure a SIP trunk end-to-end for ElevenLabs, Vapi, or Retell agents.",
  "totalTime": "PT45M",
  "tool": [
    { "@type": "HowToTool", "name": "DIDWW account" },
    { "@type": "HowToTool", "name": "ElevenLabs agent" }
  ],
  "step": [
    {
      "@type": "HowToStep",
      "name": "Provision DID number",
      "text": "Log into the DIDWW portal and order a local DID in your target country.",
      "url": "https://example.com/guide#step-1"
    },
    {
      "@type": "HowToStep",
      "name": "Configure SIP endpoint",
      "text": "Set the SIP endpoint to your agent platform's inbound URL with credentials.",
      "url": "https://example.com/guide#step-2"
    }
  ]
}
</script>
```

## Product

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "FitBeat Music — Pro subscription",
  "image": ["https://fitbeat.music/product.jpg"],
  "description": "Music-powered interval training with automatic BPM matching.",
  "brand": { "@type": "Brand", "name": "FitBeat Music" },
  "sku": "pro-monthly",
  "gtin": "01234567890123",
  "offers": {
    "@type": "Offer",
    "url": "https://apps.apple.com/us/app/fitbeat-music/id6757625699",
    "priceCurrency": "USD",
    "price": "9.99",
    "priceValidUntil": "2026-12-31",
    "availability": "https://schema.org/InStock",
    "itemCondition": "https://schema.org/NewCondition"
  },
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.7",
    "reviewCount": "183"
  }
}
</script>
```

## Review / AggregateRating

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Review",
  "itemReviewed": {
    "@type": "Product",
    "name": "FitBeat Music"
  },
  "author": { "@type": "Person", "name": "Jordan Lee" },
  "datePublished": "2026-04-10",
  "reviewRating": {
    "@type": "Rating",
    "ratingValue": "5",
    "bestRating": "5",
    "worstRating": "1"
  },
  "reviewBody": "Best music app I've tried for HIIT. The tempo-matching actually works — tracks stretch cleanly to my pace."
}
</script>
```

## Recipe

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Recipe",
  "name": "Classic Tomato Basil Pasta",
  "image": "https://example.com/pasta.jpg",
  "author": { "@type": "Person", "name": "Chef Maria" },
  "datePublished": "2026-02-14",
  "description": "A 15-minute weeknight pasta with fresh tomatoes and basil.",
  "prepTime": "PT5M",
  "cookTime": "PT10M",
  "totalTime": "PT15M",
  "recipeYield": "4 servings",
  "recipeCategory": "Main course",
  "recipeCuisine": "Italian",
  "nutrition": {
    "@type": "NutritionInformation",
    "calories": "420 calories"
  },
  "recipeIngredient": [
    "1 lb spaghetti",
    "4 ripe tomatoes, diced",
    "1/2 cup fresh basil",
    "3 cloves garlic",
    "4 tbsp olive oil",
    "salt and pepper to taste"
  ],
  "recipeInstructions": [
    { "@type": "HowToStep", "text": "Boil pasta in salted water per package directions." },
    { "@type": "HowToStep", "text": "Sauté garlic in olive oil; add tomatoes and simmer 5 minutes." },
    { "@type": "HowToStep", "text": "Toss pasta with sauce and basil; season and serve." }
  ],
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.8",
    "reviewCount": "312"
  }
}
</script>
```

## Event

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Event",
  "name": "Voice AI Summit 2026",
  "startDate": "2026-09-15T09:00:00-07:00",
  "endDate": "2026-09-17T17:00:00-07:00",
  "eventStatus": "https://schema.org/EventScheduled",
  "eventAttendanceMode": "https://schema.org/MixedEventAttendanceMode",
  "location": [
    {
      "@type": "Place",
      "name": "Moscone West",
      "address": {
        "@type": "PostalAddress",
        "streetAddress": "800 Howard St",
        "addressLocality": "San Francisco",
        "addressRegion": "CA",
        "postalCode": "94103",
        "addressCountry": "US"
      }
    },
    {
      "@type": "VirtualLocation",
      "url": "https://example.com/voice-ai-summit-livestream"
    }
  ],
  "image": ["https://example.com/event-hero.jpg"],
  "description": "Three days on voice AI infrastructure, agents, and deployment.",
  "offers": {
    "@type": "Offer",
    "url": "https://example.com/tickets",
    "price": "799",
    "priceCurrency": "USD",
    "availability": "https://schema.org/InStock",
    "validFrom": "2026-04-01T09:00:00-07:00"
  },
  "performer": { "@type": "PerformingGroup", "name": "Industry Panel" },
  "organizer": { "@type": "Organization", "name": "Example Corp", "url": "https://example.com" }
}
</script>
```

## Course

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Course",
  "name": "Voice AI Infrastructure Fundamentals",
  "description": "8-week asynchronous program covering SIP, codecs, agent platforms, and deployment.",
  "provider": {
    "@type": "Organization",
    "name": "Example Academy",
    "sameAs": "https://academy.example.com"
  },
  "hasCourseInstance": {
    "@type": "CourseInstance",
    "courseMode": "online",
    "startDate": "2026-06-01",
    "endDate": "2026-07-27",
    "courseWorkload": "PT30H",
    "instructor": {
      "@type": "Person",
      "name": "Jane Smith"
    }
  },
  "offers": {
    "@type": "Offer",
    "price": "499",
    "priceCurrency": "USD",
    "availability": "https://schema.org/InStock"
  }
}
</script>
```

## VideoObject

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "VideoObject",
  "name": "How to pick a SIP trunking provider in 2026",
  "description": "A 5-minute framework for evaluating global DID carriers.",
  "thumbnailUrl": "https://example.com/video-thumb.jpg",
  "uploadDate": "2026-03-15T08:00:00+00:00",
  "duration": "PT5M12S",
  "contentUrl": "https://example.com/videos/pick-sip-provider.mp4",
  "embedUrl": "https://www.youtube.com/embed/abc123",
  "publisher": {
    "@type": "Organization",
    "@id": "https://example.com/#organization"
  },
  "hasPart": [
    {
      "@type": "Clip",
      "name": "Chapter 1: Licensing",
      "startOffset": 0,
      "endOffset": 72,
      "url": "https://example.com/videos/pick-sip-provider.mp4#t=0"
    },
    {
      "@type": "Clip",
      "name": "Chapter 2: Pricing",
      "startOffset": 72,
      "endOffset": 180,
      "url": "https://example.com/videos/pick-sip-provider.mp4#t=72"
    }
  ]
}
</script>
```

## SoftwareApplication / MobileApplication

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "MobileApplication",
  "name": "FitBeat Music",
  "operatingSystem": "iOS",
  "applicationCategory": "HealthApplication",
  "offers": {
    "@type": "Offer",
    "price": "9.99",
    "priceCurrency": "USD"
  },
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.7",
    "reviewCount": "183"
  },
  "author": { "@type": "Person", "name": "Alex Pritsert" },
  "downloadUrl": "https://apps.apple.com/us/app/fitbeat-music/id6757625699",
  "screenshot": [
    "https://fitbeat.music/screens/home.png",
    "https://fitbeat.music/screens/workout.png"
  ],
  "softwareVersion": "1.1.0",
  "releaseNotes": "Improved BPM detection accuracy for sub-120 BPM tracks.",
  "fileSize": "111MB",
  "storageRequirements": "200MB free"
}
</script>
```

## Service

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Service",
  "name": "Global SIP trunking",
  "provider": {
    "@type": "Organization",
    "@id": "https://didww.com/#organization"
  },
  "areaServed": [
    { "@type": "Country", "name": "Germany" },
    { "@type": "Country", "name": "France" },
    { "@type": "Country", "name": "United Kingdom" }
  ],
  "serviceType": "Telecommunications",
  "description": "Enterprise SIP trunking with own numbering in 18 countries and telecom licenses in 29.",
  "offers": {
    "@type": "Offer",
    "priceSpecification": {
      "@type": "UnitPriceSpecification",
      "price": "0.0035",
      "priceCurrency": "USD",
      "unitText": "per minute"
    }
  }
}
</script>
```

## JobPosting

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "JobPosting",
  "title": "Senior Voice Infrastructure Engineer",
  "description": "<p>Join our team as a Senior Voice Infrastructure Engineer...</p>",
  "identifier": {
    "@type": "PropertyValue",
    "name": "Example Corp",
    "value": "svie-2026-04"
  },
  "datePosted": "2026-04-18",
  "validThrough": "2026-05-31T23:59:59+00:00",
  "employmentType": "FULL_TIME",
  "hiringOrganization": {
    "@type": "Organization",
    "name": "Example Corp",
    "sameAs": "https://example.com"
  },
  "jobLocation": {
    "@type": "Place",
    "address": {
      "@type": "PostalAddress",
      "streetAddress": "123 Main St",
      "addressLocality": "San Francisco",
      "addressRegion": "CA",
      "postalCode": "94105",
      "addressCountry": "US"
    }
  },
  "baseSalary": {
    "@type": "MonetaryAmount",
    "currency": "USD",
    "value": {
      "@type": "QuantitativeValue",
      "minValue": 170000,
      "maxValue": 220000,
      "unitText": "YEAR"
    }
  },
  "jobLocationType": "TELECOMMUTE"
}
</script>
```

## BreadcrumbList

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "name": "Home",
      "item": "https://example.com"
    },
    {
      "@type": "ListItem",
      "position": 2,
      "name": "Guides",
      "item": "https://example.com/guides"
    },
    {
      "@type": "ListItem",
      "position": 3,
      "name": "SIP Trunking",
      "item": "https://example.com/guides/sip-trunking"
    }
  ]
}
</script>
```

## Dataset

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Dataset",
  "name": "State of Voice AI 2026 Survey Data",
  "description": "Responses from 1,247 enterprise buyers on voice AI infrastructure choices.",
  "url": "https://example.com/state-of-voice-ai-2026",
  "sameAs": "https://doi.org/10.xxxx/example",
  "keywords": ["voice AI", "SIP", "enterprise telephony"],
  "creator": {
    "@type": "Organization",
    "@id": "https://example.com/#organization"
  },
  "temporalCoverage": "2026-01-01/2026-03-31",
  "spatialCoverage": "Global",
  "license": "https://creativecommons.org/licenses/by/4.0/",
  "distribution": [
    {
      "@type": "DataDownload",
      "encodingFormat": "text/csv",
      "contentUrl": "https://example.com/data/voice-ai-2026.csv"
    },
    {
      "@type": "DataDownload",
      "encodingFormat": "application/json",
      "contentUrl": "https://example.com/data/voice-ai-2026.json"
    }
  ]
}
</script>
```

## Book

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Book",
  "name": "The Voice Stack: Infrastructure for AI Agents",
  "author": {
    "@type": "Person",
    "@id": "https://example.com/authors/jane-smith#person"
  },
  "isbn": "978-1234567890",
  "bookFormat": "https://schema.org/Paperback",
  "numberOfPages": "328",
  "publisher": {
    "@type": "Organization",
    "name": "Example Press"
  },
  "datePublished": "2025-10-01",
  "image": "https://example.com/book-cover.jpg",
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.6",
    "reviewCount": "42"
  }
}
</script>
```

## AggregateOffer

For product category pages listing multiple variants:

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "DID numbers",
  "offers": {
    "@type": "AggregateOffer",
    "offerCount": "500000",
    "lowPrice": "0.50",
    "highPrice": "50.00",
    "priceCurrency": "USD"
  }
}
</script>
```

## SearchAction (sitelinks search box)

Embedded in the WebSite schema above. Google uses this to render a search box directly in the SERP for brand queries.

---

## Implementation patterns

### Linking schemas via `@id`

Use `@id` to reference entities across multiple schema blocks on the same or related pages. This creates a graph instead of isolated schema blocks.

```html
<!-- Organization on homepage -->
<script type="application/ld+json">
{
  "@type": "Organization",
  "@id": "https://example.com/#organization",
  ...
}
</script>

<!-- Article on any page references the organization -->
<script type="application/ld+json">
{
  "@type": "Article",
  "publisher": { "@id": "https://example.com/#organization" },
  ...
}
</script>
```

### @graph for multiple schemas on one page

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    { "@type": "Organization", "@id": "...#organization", ... },
    { "@type": "WebSite", "@id": "...#website", ... },
    { "@type": "Article", "@id": "...#article", ... },
    { "@type": "BreadcrumbList", ... }
  ]
}
</script>
```

Cleaner than four separate `<script>` blocks. Google parses both equally well.

### Validation

Test every change:

```bash
# Rich Results Test (Google)
open "https://search.google.com/test/rich-results?url=$(python3 -c 'import urllib.parse; print(urllib.parse.quote(\"https://example.com/page\"))')"

# Schema.org validator (official)
open "https://validator.schema.org/#url=$(python3 -c 'import urllib.parse; print(urllib.parse.quote(\"https://example.com/page\"))')"
```

## Anti-patterns

- Schema doesn't reflect visible content (e.g., rating in schema, no rating visible) → manual penalty
- Stale `dateModified` that never updates → freshness signal lost
- Missing `sameAs` in Organization → entity disambiguation weak
- Multiple conflicting schemas on one page (two `Organization` with different `name`) → confused parser
- Hardcoded `aggregateRating` with no actual review infrastructure → fraud
- FAQ schema with fake questions nobody asks → diminishing returns + risk
- Schema.org versions / vocabs mismatched → validator errors
