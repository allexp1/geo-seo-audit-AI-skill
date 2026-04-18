# E-E-A-T Implementation

Google's quality rater guidelines elevate Experience, Expertise, Authoritativeness, and Trustworthiness as signals for what gets surfaced. E-E-A-T is not a direct ranking algorithm — it's a signal cluster the algorithm approximates. Same signals heavily influence AI citation.

## The four components

### Experience (E, added 2022)

First-hand, lived experience with the subject. Google now distinguishes between "journalist who researched X" and "person who has done X."

**Signals of experience:**
- First-person language where appropriate ("I tested this for 3 months...")
- Original photography (not stock)
- Screenshots from actual use
- Specific measurements, timings, prices the author observed
- Methodology descriptions ("I tested X by doing Y")

**Weak examples:**
- "According to many sources..."
- Stock photos
- Generic comparisons copied from press releases

**Strong examples:**
- "I tested FitBeat Music on a 5K run with an Apple Watch. At 165 BPM pace, the app pitched 'Neon Spirit' from 140 to 160 BPM — the pitch-shift was audibly clean. See the waveform below."
- Original screenshots, timestamps
- "My invoice for 3 months was $29.97 — here's the PDF"

### Expertise (E)

Documented qualifications to discuss the subject.

**Signals:**
- Author bylines on every page
- Author bio page with credentials (`/authors/jane-smith`)
- `Person` schema with `alumniOf`, `jobTitle`, `worksFor`
- LinkedIn profile visible and consistent
- Published book, course, or widely-cited research
- Industry certifications (CFA, CPA, MD, board certifications)

### Authoritativeness (A)

Recognized by others as the go-to source.

**Signals:**
- Backlinks from known experts / institutions
- Wikipedia / Wikidata references
- Citations in academic papers (Google Scholar)
- Media mentions in Tier 1 outlets
- Speaking at industry conferences
- "sameAs" links to recognized identity platforms

### Trustworthiness (T)

Most important of the four per Google's own guidelines.

**Signals:**
- HTTPS
- Privacy policy + Terms of Service (real ones, not template copy)
- Clear ownership (business registration, real address, real phone)
- Transparent funding (disclose sponsorships, affiliates)
- Reviews from real users
- No deceptive practices (hidden fees, bait-and-switch)
- Security (no breaches, no malware)

## Implementation checklist per page

### Every content page

- [ ] Byline with author name linked to author bio page
- [ ] Date published + date modified visible
- [ ] Editor / fact-checker credit where applicable
- [ ] Source citations (hyperlinked to authoritative sources)
- [ ] Author bio snippet (1-2 sentences) beneath or beside byline
- [ ] Schema: `Article` with full `author` + `publisher` blocks

### Every product / service page

- [ ] Company / founder named
- [ ] Real contact information (not just form)
- [ ] Verifiable claims (with data, not just marketing copy)
- [ ] Customer reviews from real users
- [ ] Schema: `Organization` or `LocalBusiness` with `sameAs` array

### Author bio page (dedicated URL)

```html
<!-- /authors/jane-smith -->
<h1>Jane Smith</h1>
<img src="jane-smith.jpg" alt="Jane Smith">
<p><strong>Senior Voice Infrastructure Analyst</strong></p>
<p>Jane has spent 12 years covering telecommunications and voice infrastructure.
Former Director of Product at Twilio (2015-2020). Graduate of MIT EECS (2013).
Quoted in The Information, Bloomberg, and Wired. Author of "The Voice Stack" (2024).</p>

<h2>Credentials</h2>
<ul>
  <li>MIT, BS Electrical Engineering & Computer Science, 2013</li>
  <li>Certified Cisco Voice Specialist (2015, renewed 2023)</li>
  <li>Previously: Director of Product, Twilio (2015–2020)</li>
</ul>

<h2>Published work</h2>
<ul>
  <li><a href="/articles/sip-trunk-audit">How to audit a SIP trunk deployment</a></li>
  ...
</ul>

<h2>Connect</h2>
<ul>
  <li><a href="https://linkedin.com/in/janesmith">LinkedIn</a></li>
  <li><a href="https://twitter.com/janesmithvoice">Twitter</a></li>
  <li><a href="https://github.com/janesmith">GitHub</a></li>
</ul>

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Person",
  "name": "Jane Smith",
  "image": "https://example.com/jane-smith.jpg",
  "jobTitle": "Senior Voice Infrastructure Analyst",
  "worksFor": {
    "@type": "Organization",
    "name": "Example Voice Research"
  },
  "alumniOf": [
    { "@type": "EducationalOrganization", "name": "MIT" }
  ],
  "sameAs": [
    "https://linkedin.com/in/janesmith",
    "https://twitter.com/janesmithvoice",
    "https://github.com/janesmith"
  ],
  "knowsAbout": ["SIP trunking", "Voice infrastructure", "CPaaS"],
  "url": "https://example.com/authors/jane-smith"
}
</script>
```

## Categories where E-E-A-T matters most

Google's "Your Money or Your Life" (YMYL) categories trigger the highest E-E-A-T scrutiny:

- Health / medical
- Finance / investing / insurance
- Legal
- News / civic
- Safety (child safety, disaster info)
- Major purchase decisions (home, car, education)

In YMYL categories, E-E-A-T is effectively a minimum bar, not a nice-to-have. Content without verifiable expertise will underperform regardless of quality.

In non-YMYL (recipes, entertainment reviews, hobby content), E-E-A-T still matters but is less determinative.

## The "who wrote this?" test

Open any of your content pages. Answer within 5 seconds:

1. Who wrote this?
2. What credentials do they have to write about this?
3. Who owns the site?
4. How do I contact them?

If any answer requires >5 seconds of scrolling/clicking, E-E-A-T fails for the page.

## AEO: why E-E-A-T matters for AI citation

LLMs inherit Google's training data and its quality heuristics. A page with:
- Clear author bio + credentials
- `Person` + `Organization` schema
- Cited by authoritative external sources
- Consistent identity across Wikipedia/Wikidata/LinkedIn

...gets cited more often than a page with:
- Anonymous or "editorial team" byline
- No schema
- Low authority profile
- Inconsistent identity

AI sees "bio page + LinkedIn + schema + consistent Wikidata entity" as a high-trust node. Invisible authors are high-risk citations (AI may hallucinate facts from them) — models increasingly avoid low-trust sources.

## Common pitfalls

- "Editorial team" as the only byline on every article → no author authority
- Bio page one line long → thin expertise signal
- Different author name in byline vs. schema vs. LinkedIn → confusion, low trust
- AI-generated content without disclosure → detection risk
- Claiming credentials not held → manual action + legal risk
- No fact-checking process → errors accumulate, reputation decays
- Privacy policy copied from a template with wrong company name → basic trust failure

## Practical quarterly cadence

**Q1:** Audit all bylines. Add real author pages for top 20 traffic-driving articles.
**Q2:** Add `Person` schema + LinkedIn links site-wide. Earn 2-3 external citations of authors.
**Q3:** Update author bios with new credentials, speaking, published work.
**Q4:** External-authority push — guest podcast appearances, conference talks, media quotes.

## Audit checklist

- [ ] Every content page has named author byline
- [ ] Every author has dedicated bio page with schema
- [ ] Organization schema with full `sameAs` array on homepage
- [ ] Privacy Policy + Terms of Service unique (not copied template)
- [ ] Real business address + phone visible (not just a form)
- [ ] Reviews / testimonials from real customers visible
- [ ] No affiliate / sponsored content without disclosure
- [ ] HTTPS + no mixed content
- [ ] YMYL categories (if applicable) have additional expert credentialing
- [ ] Authors linked to LinkedIn / Wikidata consistently
