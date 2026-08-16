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
