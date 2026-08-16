# Santosh Sikarwar — Website

Personal website for Santosh Sikarwar, served via GitHub Pages at
[santoshsikarwar.in](https://santoshsikarwar.in).

## Structure

- `index.html` — page content (edit your text here)
- `styles.css` — styling / colors
- `script.js` — small interactions (menu, footer year)
- `CNAME` — tells GitHub Pages to use the custom domain

## Edit locally

Open `index.html` in any browser to preview. Edit the files, save, then push:

```bash
git add .
git commit -m "Update content"
git push
```

Changes go live automatically within a minute or two.

---

# SEO, Analytics & Search Console Guide

This site is a static site hosted on GitHub Pages at **https://santoshsikarwar.in/**.
The following technical SEO is already implemented in the code.

## What is already implemented
- Unique `<title>` + meta description, canonical URL, meta robots
- Open Graph + Twitter/X Card metadata + `og:image` (`images/og-image.jpg`)
- Favicon, apple-touch-icon, `manifest.webmanifest`, theme color
- JSON-LD structured data: **Person**, **PoliticalParty** (BJP), **WebSite**, and **BreadcrumbList** (legal pages)
- `robots.txt` (blocks `/admin/`) and `sitemap.xml`
- Semantic HTML, one `<h1>` on the homepage, logical H2/H3, alt text, skip link, focus states
- Custom branded `404.html` (returns HTTP 404 on GitHub Pages)
- Legal pages: `privacy-policy.html`, `terms.html`, `disclaimer.html`
- Image SEO: hero image `fetchpriority="high"` + width/height (reduces CLS); gallery/feed images lazy-loaded with descriptive alt

## 1) Google Search Console (GSC) setup
1. Go to https://search.google.com/search-console and sign in.
2. Add property → **URL prefix** → enter `https://santoshsikarwar.in/`.
3. Verify ownership. Easiest for this setup:
   - Choose **HTML tag** verification. Google gives a tag like
     `<meta name="google-site-verification" content="XXidXX" />`.
   - Send me that content value (or paste the tag) and I will add it to `<head>` of `index.html`.
   - (Do NOT commit a fake code — only the real one Google gives you.)
4. After verification, go to **Sitemaps** → enter `sitemap.xml` → **Submit**.
5. Use **URL Inspection** → paste `https://santoshsikarwar.in/` → **Request Indexing**.
6. Monitor: **Pages** (indexing), **Performance** (search queries/clicks), **Experience → Core Web Vitals**.

## 2) Google Analytics 4 (GA4) setup
1. Create a GA4 property at https://analytics.google.com and get your **Measurement ID** (`G-XXXXXXXXXX`).
2. Open `script.js`, find the line near the top:
   ```js
   const GA_MEASUREMENT_ID = ""; // <-- put your real GA4 ID here
   ```
   Put your real ID in the quotes and save.
3. Commit & push (or edit the file directly on GitHub). Analytics loads only when an ID is set — no fake IDs.
4. Custom events already wired: `phone_click`, `contact_click`, `social_profile_click`, `gallery_open`.
   (Standard `page_view` is automatic.)

## 3) Social sharing image
`images/og-image.jpg` currently reuses the profile photo. For the best link previews
on WhatsApp/Facebook/X, replace it with a **1200×630 px** branded image named exactly
`images/og-image.jpg` (upload via GitHub or the admin panel).

## 4) Security headers (important limitation)
GitHub Pages is static hosting and **cannot set custom HTTP response headers**
(CSP, X-Content-Type-Options, HSTS, Permissions-Policy). What we did:
- `Referrer-Policy` is set via a `<meta name="referrer">` tag.
- HTTPS is enforced by GitHub Pages ("Enforce HTTPS").
To add full security headers, front the site with **Cloudflare** (free) and set headers
via Cloudflare Rules / Transform Rules. Ask me and I can guide this.

## 5) Google Business Profile
No public office address is published on this site, so no `LocalBusiness` schema was added
(adding fake local markup violates Google guidelines). If a genuine public office address
becomes available, it can be added to the Person schema and a Google Business Profile created.

## 6) Optional future step — multi-page structure
The site is intentionally a single strong page with in-page sections (`/#about`,
`/#journey`, etc.). If separate indexable routes (`/parichay`, `/rajnitik-yatra`, …) are
later desired, that is a larger change that can be layered on with a static-site generator
without losing the current design.

## Manual steps you still need to do
- [ ] Verify domain in Google Search Console and send me the verification code (or add it yourself).
- [ ] Submit `sitemap.xml` in GSC.
- [ ] Create a GA4 property and paste the Measurement ID into `script.js`.
- [ ] (Optional) Add a dedicated 1200×630 `images/og-image.jpg`.
- [ ] Confirm real email & phone in the admin panel (currently placeholders).

---

# News & Activities — Publishing Workflow

The news/activity system is CMS-driven. Content lives in `data/feed.json` and is
rendered on the homepage (latest) and at `/samachar/` (archive + individual articles).

## Add a genuine activity/news item
1. Open **https://santoshsikarwar.in/admin/** and log in.
2. Go to **समाचार / गतिविधियाँ → समाचार सूची** and click **Add समाचार / गतिविधि**.
3. Fill in (use only real information):
   - **शीर्षक** (title) — the actual event/activity title
   - **तारीख** (date) — the real event date (stored as YYYY-MM-DD)
   - **स्थान** (location) — e.g. "आगरा, उत्तर प्रदेश" (leave empty if not applicable; never a private address)
   - **श्रेणी** (category) — कार्यक्रम / जनसंपर्क / संगठनात्मक गतिविधि / सामाजिक गतिविधि / बैठक / सम्मान / अन्य
   - **मुख्य फ़ोटो** (featured image) — upload with a descriptive filename, e.g. `santosh-sikarwar-agra-programme.jpg`
   - **संक्षिप्त विवरण** (excerpt) — 1–2 line summary shown on cards
   - **पूरा विवरण** (full body)
   - **गैलरी फ़ोटो** (optional) — add multiple photos with captions
   - **लेखक/स्रोत**, **मुख्य (featured)?**, **प्रकाशित करें?** (uncheck to keep hidden), **अद्यतन तिथि** (if edited later)
4. Keep **प्रकाशित करें?** ON to publish; OFF keeps it hidden from the public site.
5. Click **Publish → Publish now**. Live in ~1–2 minutes.
6. Verify the article at `https://santoshsikarwar.in/samachar/?slug=<your-slug>`.

## After publishing (for fast indexing)
Because GitHub Pages has no build step, the **sitemap is updated manually**:
1. Edit `sitemap.xml` and add the new article URL:
   ```xml
   <url><loc>https://santoshsikarwar.in/samachar/?slug=YOUR-SLUG</loc><lastmod>YYYY-MM-DD</lastmod><priority>0.6</priority></url>
   ```
2. Commit/push (or edit on GitHub).
3. In Google Search Console → **URL Inspection** → paste the article URL → **Request Indexing**.

## Slugs
Give each item a short English **slug** (lowercase, hyphens), e.g. `agra-karyakarta-baithak`.
If left blank, the article is still reachable via `/samachar/?id=<index>`, but a slug is
recommended for clean, memorable URLs.

## Architecture note & limitation (important)
- Article pages are **client-rendered** from `feed.json` at `/samachar/?slug=…`.
  Google renders JavaScript, so these pages are crawlable/indexable, and each gets a
  correct canonical + `NewsArticle` JSON-LD + title/description at runtime.
- **Limitation:** social scrapers (WhatsApp/Facebook/X) generally do **not** execute
  JavaScript, so per-article link previews fall back to the site's default share image,
  not the article's own image. The homepage and archive share correctly.
- **Future upgrade (optional, not a rebuild-now):** to get per-article static OG images
  and clean `/samachar/[slug]` URLs, introduce a lightweight static-site generator
  (e.g. Eleventy/Astro) that pre-renders each `feed.json` entry to its own HTML file at
  build time. This keeps Decap CMS and the current design while adding a build step.

## RSS
An RSS `/feed.xml` was intentionally **not** added: without a build step it would go stale
and risk serving outdated content. It can be added later alongside the SSG upgrade above.

---

# Content Quality, Maintenance & Long-Term Strategy

## Pre-publish checklist (every genuine activity)
Before setting **प्रकाशित करें = ON**, verify:
- [ ] Real event **date** (YYYY-MM-DD)
- [ ] Correct **title** (no exaggeration)
- [ ] **Location** (only if genuinely public; never a private/residential address)
- [ ] Authentic **photograph** with a descriptive filename + accurate caption
- [ ] Correct **names, designation, organization** spelling — always "Santosh Sikarwar", "जिला उपाध्यक्ष, भारतीय जनता पार्टी, आगरा"
- [ ] Any **quotation** is accurate and correctly attributed
- [ ] Factual **description** — no invented achievements, statistics, endorsements, or news

Never publish fabricated political information. AI may help with grammar/formatting/summarizing owner-supplied facts, never with inventing them.

## Recommended image specs
- **Featured image:** ~1200px wide, compressed JP/WebP, under ~300 KB, descriptive filename
  (e.g. `santosh-sikarwar-agra-programme.jpg`), meaningful alt/caption.
- **Gallery:** compressed, lazy-loaded automatically, captions where useful.
- Avoid uploading raw multi-MB camera files; resize first. Do not stretch/distort photos.
- The social fallback image `images/og-image.jpg` stays **1200×630** and must return HTTP 200.

## Content roadmap (all genuine only)
Public programmes · organizational activities · meetings · social activities · public events ·
authentic photographs · factual political-journey updates.
Avoid: AI filler, fake news, keyword stuffing, duplicate articles.

## Draft/publish behaviour (verified)
`published: false` → hidden from homepage feed, latest strip, archive, related, and should be
kept out of `sitemap.xml`. `published: true` → visible through the normal flow.
An invalid or unpublished `?slug=` shows a professional "यह समाचार उपलब्ध नहीं है" page (noindex).

## Google Knowledge Panel — honest expectation
Structured data and consistent identity **strengthen entity signals but cannot guarantee** a
Knowledge Panel. Long-term strategy: official website + consistent official social profiles +
accurate structured data + a genuine public-activity archive + legitimate external references +
consistent identity information. No guarantees.

## Future SSG migration (do NOT do now)
A lightweight static-site generator (Eleventy/Astro) could later pre-render each `feed.json`
entry to its own static HTML file, giving: clean `/samachar/[slug]` URLs, **article-specific
static OG metadata** (fixes the social-crawler limitation), automatic sitemap generation, and
no client-render dependency — while keeping Decap CMS and the current visual design.

## Known limitation — social link previews
Article pages are client-rendered, so WhatsApp/Facebook/X scrapers (which don't run JS) fall
back to the site's default `og-image.jpg` and default title rather than the article's own image.
Google indexes articles fine (it renders JS). The SSG migration above is the clean future fix.

---

# FINAL LAUNCH GUIDE (production)

## Publishing a genuine activity/news article — checklist
```
[ ] Correct title (real, no exaggeration)
[ ] Correct date (YYYY-MM-DD)
[ ] Correct location (public only; never a private residential address)
[ ] Correct names / designation / organization
[ ] Genuine photograph(s), descriptive filename + alt/caption
[ ] Accurate factual description
[ ] Hindi content checked
[ ] English version checked (if provided)
[ ] No fabricated claims / statistics / awards
[ ] Publish (प्रकाशित करें = ON) in Decap CMS
[ ] Verify the live page: https://santoshsikarwar.in/samachar/?slug=YOUR-SLUG
[ ] Confirm title/description/canonical/OG look correct
[ ] (Optional) Request indexing in Google Search Console
```

## Google Search Console — exact steps
1. https://search.google.com/search-console → add property → **URL prefix** → `https://santoshsikarwar.in/`.
2. Verify ownership (HTML tag method): paste the tag into `<head>` of `index.html` at the marked
   comment `<!-- Google Search Console ... -->`. (Only the real code Google gives you.)
3. **Sitemaps** → submit `sitemap.xml` (full URL `https://santoshsikarwar.in/sitemap.xml` if the short form is rejected).
4. **URL Inspection** → paste the homepage → **Request Indexing**.
5. Monitor **Pages** (indexing), **Experience → Core Web Vitals**, **Security & Manual Actions**.
Do not request indexing for the same URL repeatedly.

## Indexing workflow for a new article
Publish → verify page loads → verify canonical + metadata → (articles are discovered via
internal links from the homepage feed and `/samachar/`) → optionally URL-Inspect + Request Indexing.

## Sitemap policy (GitHub Pages, no build step)
`sitemap.xml` lists only canonical indexable documents: homepage, `/samachar/` archive, and the
legal pages. It intentionally does **not** list per-article query URLs. New articles are found by
Google through internal links (Google renders the JS). If you later adopt a static-site generator,
each article can get its own clean URL + sitemap entry automatically.

## Cache-busting workflow
CSS/JS are linked with a version query, e.g. `styles.css?v=9`, `script.js?v=9`.
**After changing `styles.css` or `script.js`, increment the number** on the pages that use them
(`index.html`, `samachar/index.html`, legal pages) so browsers fetch the fresh file.
Do not add version queries to images or other assets unnecessarily.

## Entity strategy (honest)
Stronger Google entity recognition comes from: this official website + consistent official social
profiles (Facebook/Instagram/X already linked) + accurate biography + valid structured data +
genuine public-activity archive with real photographs + legitimate external references + consistent
identity everywhere. This **cannot guarantee** a Google Knowledge Panel; it builds the right signals.

## Growth
Grow the site only with genuine material (programmes, meetings, social/organisational activities,
public events, real photographs, verified updates). No AI-generated filler, fake news, or fabricated
achievements.
