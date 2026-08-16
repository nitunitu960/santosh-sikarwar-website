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

## After publishing — run the sitemap generator (one command)
The three sitemaps are **generated from `data/feed.json`**, never edited by hand:
```bash
python generate_sitemaps.py
```
This regenerates `sitemap.xml`, `image-sitemap.xml`, and `news-sitemap.xml` from the
published posts. Then review the output, check `git diff`, and commit/push.
See **“Automated Sitemap Generation”** below for full details.

Requesting indexing in Search Console is **optional** (Google also finds new articles
through the submitted sitemap + internal links). Do it only if you want a fresh article
noticed faster: **URL Inspection** → paste the article URL → **Request Indexing** (once).

## Slugs
Give each item a short English **slug** (lowercase, hyphens), e.g. `agra-karyakarta-baithak`.
If left blank, the article is still reachable via `/samachar/?id=<index>` (and the generator
will warn you), but a slug is strongly recommended for a clean, **stable** URL.

---

# Automated Sitemap Generation

`data/feed.json` is the **single source of truth**. A small script reads it and generates all
three sitemaps deterministically — you never hand-edit `sitemap.xml`, `image-sitemap.xml`, or
`news-sitemap.xml` again.

## One command
```bash
python generate_sitemaps.py
```
Requires Python 3 (already available on the maintainer's machine). No frameworks, no packages —
standard library only. It reads `data/feed.json` (and `data/settings.json` for the homepage hero
image) and writes the three XML files in the repo root.

Helpful flags:
- `python generate_sitemaps.py --check` — report what *would* change without writing (exit code 1 if anything differs). Good for a pre-commit sanity check.
- `python generate_sitemaps.py --today 2026-08-16` — override “today” for the news window (testing only).

## What it generates
- **`sitemap.xml`** — homepage, `/samachar/` archive, the three legal pages, **plus every published
  article URL** (`/samachar/?slug=…`, with `<lastmod>` from the post's `updated_at` or `date`).
  Unpublished posts, admin, 404, and duplicates are excluded.
- **`image-sitemap.xml`** — homepage hero + portrait, and each published article's **featured image +
  gallery images**, mapped to the page they actually appear on. Images whose files are missing from
  the repo are skipped (no broken/placeholder paths). Only images referenced by published content.
- **`news-sitemap.xml`** — only articles whose **original publication date** is within the previous
  **2 days** (Google News guidance). `updated_at` is never used to fake freshness. If none qualify,
  a valid **empty** `<urlset>` is written.

## Guarantees
- **Deterministic:** the same `feed.json` produces byte-identical XML on a given day. No generation
  timestamps are embedded; article `<lastmod>` comes from the feed data. Running it twice without
  changing `feed.json` yields **no git diff**.
- **Published-only:** anything with `published: false` is omitted everywhere.
- **Validation with warnings:** missing title, missing/invalid slug, missing/invalid date, duplicate
  slugs/URLs, and missing image files each print a clear `!` warning instead of silently producing a
  broken sitemap. Review warnings before committing.
- **Absolute HTTPS URLs** only, canonical base `https://santoshsikarwar.in/`.

## It does NOT touch anything else
The generator only **reads** `feed.json`/`settings.json` and **writes** the three XML files. It does
not modify Decap CMS config, the `feed.json` schema, admin authentication, article rendering, SEO
metadata, or existing article URLs.

## Deployment reality (important, honest)
GitHub Pages is **static** — it does **not** run this script or regenerate sitemaps after a CMS
publish. The generator runs **on your computer before deployment**, and the resulting XML files are
committed and pushed like any other file. That is by design.

## Future option (not implemented on purpose)
This same script could later be wired into a **GitHub Actions** workflow to run automatically on
every push (so publishing via the CMS would trigger regeneration server-side). That adds CI
infrastructure and is intentionally **not** set up now to keep things simple. It can be added later
without changing the generator itself.

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
[ ] Run: python generate_sitemaps.py
[ ] Review the 3 sitemaps + `git diff`, then commit & push
[ ] Verify the live page: https://santoshsikarwar.in/samachar/?slug=YOUR-SLUG
[ ] Confirm title/description/canonical/OG look correct
[ ] (Optional, not required) Request indexing in Google Search Console
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

## Sitemap policy (generated from feed.json)
All three sitemaps are produced by `python generate_sitemaps.py` from `data/feed.json` — never
edited by hand. `sitemap.xml` lists the homepage, `/samachar/` archive, the legal pages, and every
**published** article URL (`/samachar/?slug=…`). Unpublished posts, admin, 404, and duplicates are
excluded automatically. See **“Automated Sitemap Generation”** above.

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

---

# SEARCH, IMAGES & DISCOVER — SEO FOUNDATION

The goal: help Google clearly understand **who** (Santosh Sikarwar), **where** (Agra, Uttar Pradesh),
**association** (Bharatiya Janata Party), and **what the site contains** (profile, political journey,
responsibilities, genuine activities, photographs). Rankings, Google Images/Discover/News placement,
and Knowledge Panels are decided by Google and **cannot be guaranteed** — this only builds the
strongest legitimate foundation. No keyword stuffing, doorway/thin pages, or fabricated content.

## Image SEO — the long-term engine
Every genuine activity photo should live on a real article/activity page near relevant text.
When you upload an image in the CMS:
- **Descriptive filename** that matches the actual photo, e.g.
  `santosh-sikarwar-kisan-samvad-agra-2026-08-16.jpg` (rename before upload).
  Avoid `IMG_1234.jpg` / WhatsApp-style names, and don't reuse one filename for every photo.
- **Alt text** (new "फ़ोटो का विवरण / image_alt" field): describe what's genuinely visible, e.g.
  "Santosh Sikarwar at a farmers' interaction in Agra." Alt text serves accessibility first —
  do NOT stuff "BJP Agra leader" repeatedly.
- **Featured image:** prefer a real high-resolution landscape photo (≥1200px, ideally 16:9).
  Avoid tiny/compressed screenshots, watermarked stock, or the generic logo when a real photo exists.
- Gallery: add 2–8 genuine supporting photos with captions where useful.

Article structured data already uses the article's **featured photo** (not the logo) as the image,
with `max-image-preview:large` enabled — the settings Google looks at for large image previews.

## Sitemaps (three files, all in robots.txt — auto-generated)
All three are generated by `python generate_sitemaps.py` from `data/feed.json`; do not edit by hand.
- `sitemap.xml` — homepage, /samachar/ archive, legal pages, and every published article URL.
- `image-sitemap.xml` — homepage images + each published article's featured/gallery images, mapped
  to the page they appear on. Missing image files are skipped automatically (no broken/placeholder).
- `news-sitemap.xml` — only articles published in the **last 2 days** (empty-but-valid if none).
  Effective only if Google accepts the site as a news source.

Submit all three once in Google Search Console → Sitemaps (already done). After that, just rerun the
generator when you publish and push — Google re-reads the submitted sitemaps automatically.

## Article title & description guidance (natural, not stuffed)
- Title describes the real activity, e.g. "किसान संवाद कार्यक्रम — संतोष सिकरवार, आगरा" or
  "Santosh Sikarwar attends [actual event] in Agra". Use BJP/Agra only when genuinely relevant.
- Excerpt/description answers what happened, who, where, when — only if actually known.
- Each article gets a unique title/description/canonical + NewsArticle JSON-LD automatically.

## Search Console monitoring (after a few weeks of real data)
Performance → check **Queries, Pages, Impressions, Clicks, CTR, Average position**.
Switch **Search type → Image** to see image impressions/clicks/queries. If Discover data appears,
review Discover impressions/clicks. Then improve real pages that get impressions but low CTR
(better title/description/photo) — never by faking freshness (don't change dates/titles artificially).

## Entity & authority (legitimate only)
- Ensure his official Facebook/Instagram/X profiles list **santoshsikarwar.in** as the website, and
  use a consistent name, photo, and designation everywhere (this reinforces the `sameAs` signal).
- Earn references only where genuinely relevant: official organisational pages, real event pages,
  legitimate local news coverage, interviews, official announcements. **Never buy or fabricate links.**

## Current URL limitation (honest)
Article pages are client-rendered at `/samachar/?slug=…` (query URLs). These URLs **are** now listed
in `sitemap.xml` (added by the generator) and Google renders the JS to index them; they are also
reachable via internal links (homepage feed + archive). A future Eleventy/Astro migration could
produce clean `/samachar/[slug]/` pages with static HTML + static per-article OG images + better
social-crawler support. Not migrating now.
