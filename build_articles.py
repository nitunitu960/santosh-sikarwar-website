#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_articles.py
====================================================================
Pre-renders one fully static HTML page per published article so that
search engines (and social crawlers) receive complete content + SEO
metadata on the FIRST fetch, with no JavaScript execution required.

Why this exists
--------------------------------------------------------------------
The site previously served every article from a single file,
/samachar/index.html, and injected the real content client-side based
on a ?slug= query parameter. Googlebot treated those query-string
variants as duplicates of one page and left them as
"Discovered - currently not indexed". Pre-rendering a real HTML file
at a clean, unique path (/samachar/<slug>/) fixes that permanently.

Single source of truth : data/feed.json (+ data/settings.json for logo)
Generates              : samachar/<slug>/index.html  (one per published,
                         slug-eligible post)
Also cleans up         : stale samachar/<slug>/ folders whose slug is no
                         longer published (keeps the site in sync)

Design rules
--------------------------------------------------------------------
* Uses ONLY published content (published != false).
* Deterministic: same feed.json -> byte-identical HTML (no timestamps).
* Never touches feed.json, the admin panel, styles, or images.
* Each page is self-contained: full title, meta description, canonical,
  Open Graph, Twitter card, NewsArticle JSON-LD, breadcrumb JSON-LD,
  the article body, gallery, and "related" links -- all in static HTML.
* Progressive enhancement: the same samachar.js is loaded so the
  lightbox / share buttons keep working, but the page is 100% readable
  without it.

Usage
--------------------------------------------------------------------
    python build_articles.py
    python build_articles.py --check   # report changes without writing
"""

import argparse
import json
import os
import re
import sys
import shutil

BASE = "https://santoshsikarwar.in/"
ROOT = os.path.dirname(os.path.abspath(__file__))
FEED_PATH = os.path.join(ROOT, "data", "feed.json")
SETTINGS_PATH = os.path.join(ROOT, "data", "settings.json")
SAMACHAR_DIR = os.path.join(ROOT, "samachar")

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
HINDI_MONTHS = ["जनवरी", "फ़रवरी", "मार्च", "अप्रैल", "मई", "जून",
                "जुलाई", "अगस्त", "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर"]

WARNINGS = []


def warn(msg):
    WARNINGS.append(msg)


# ---------- helpers ----------
def esc(value):
    """Escape for HTML text/attribute context."""
    return (
        str(value if value is not None else "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as exc:
        print("ERROR: %s is not valid JSON: %s" % (os.path.basename(path), exc))
        sys.exit(1)


def hindi_date(value):
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", str(value or ""))
    if not m:
        return str(value or "")
    return "%d %s %s" % (int(m.group(3)), HINDI_MONTHS[int(m.group(2)) - 1], m.group(1))


def abs_img(value):
    """Normalise an image reference to an absolute URL on the site."""
    if not value:
        return ""
    v = str(value).strip()
    if re.match(r"^https?://", v):
        return v
    v = v.lstrip("/")
    if not v.startswith("images/"):
        v = "images/" + v
    return BASE + v


def excerpt_of(post):
    if post.get("excerpt"):
        return post["excerpt"]
    text = re.sub(r"\s+", " ", str(post.get("text") or "")).strip()
    return (text[:160] + "…") if len(text) > 160 else text


def clean_url(slug):
    return BASE + "samachar/" + slug + "/"


def body_html(text):
    """Convert plain text (double-newline paragraphs) to safe <p> HTML."""
    parts = re.split(r"\n{2,}", str(text or ""))
    out = []
    for p in parts:
        p = p.strip("\n")
        if p == "":
            continue
        out.append("<p>" + esc(p).replace("\n", "<br>") + "</p>")
    return "".join(out)


def published_posts(feed):
    posts = feed.get("posts", []) if isinstance(feed, dict) else []
    out = [(i, p) for i, p in enumerate(posts) if p.get("published") is not False]
    out.sort(key=lambda ip: (str(ip[1].get("date") or ""), str(ip[1].get("slug") or "")),
             reverse=True)
    return out


def eligible_posts(published):
    """Published posts with a valid, unique slug. Others are excluded + warned."""
    eligible = []
    seen = {}
    for idx, post in published:
        title = str(post.get("title") or "")[:40]
        slug = post.get("slug")
        if not slug:
            warn("post #%d ('%s'): missing slug -> no page generated" % (idx, title))
            continue
        if not SLUG_RE.match(slug):
            warn("post #%d ('%s'): invalid slug '%s' -> no page generated" % (idx, title, slug))
            continue
        if slug in seen:
            warn("post #%d ('%s'): duplicate slug '%s' (first used by #%d) -> skipped"
                 % (idx, title, slug, seen[slug]))
            continue
        seen[slug] = idx
        eligible.append((idx, post))
    return eligible


# ---------- rendering ----------
def render_card(post):
    """A feed card linking to the clean article URL (used for related list)."""
    href = "/samachar/" + post["slug"] + "/"
    img = ""
    if post.get("image"):
        img = ('<div class="feed-img"><img src="%s" alt="%s" loading="lazy" /></div>'
               % (abs_img(post["image"]), esc(post.get("image_alt") or post.get("title"))))
    meta = " · ".join(esc(x) for x in [post.get("category"), post.get("location")] if x)
    return (
        '<a class="feed-card" href="%s" aria-label="%s">%s'
        '<div class="feed-body">'
        '<span class="feed-date">%s</span>'
        '%s'
        '<h3>%s</h3>'
        '<p>%s</p>'
        '<span class="read-more">और पढ़ें →</span>'
        '</div></a>'
    ) % (
        href, esc(post.get("title")), img,
        esc(hindi_date(post.get("date"))),
        ('<span class="feed-meta">%s</span>' % meta) if meta else "",
        esc(post.get("title")),
        esc(excerpt_of(post)),
    )


def related_for(post, eligible):
    """Up to 3 related posts (same category first, then newest), excluding self."""
    slug = post["slug"]
    others = [p for (_, p) in eligible if p.get("slug") != slug]
    others.sort(key=lambda p: (
        0 if p.get("category") == post.get("category") else 1,
        # newest first within each group -> reverse date via negation trick
    ))
    # stable secondary sort by date desc
    others.sort(key=lambda p: str(p.get("date") or ""), reverse=True)
    others.sort(key=lambda p: 0 if p.get("category") == post.get("category") else 1)
    return others[:3]


def json_ld(post):
    url = clean_url(post["slug"])
    img = abs_img(post.get("image")) if post.get("image") else BASE + "images/og-image.jpg"
    desc = excerpt_of(post)
    article = {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": post.get("title"),
        "description": desc,
        "image": [img],
        "inLanguage": "hi-IN",
        "author": {"@type": "Person", "name": post.get("author") or "संतोष सिकरवार"},
        "publisher": {
            "@type": "Organization",
            "name": "Santosh Sikarwar",
            "logo": {"@type": "ImageObject", "url": BASE + "images/santosh-sikarwar.jpg"},
        },
        "about": {"@type": "Person", "@id": BASE + "#person", "name": "Santosh Sikarwar"},
        "mainEntityOfPage": {"@type": "WebPage", "@id": url},
    }
    if post.get("date"):
        article["datePublished"] = post["date"]
        article["dateModified"] = post.get("updated_at") or post["date"]
    if post.get("category"):
        article["articleSection"] = post["category"]

    breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "मुख्य पृष्ठ", "item": BASE},
            {"@type": "ListItem", "position": 2, "name": "समाचार", "item": BASE + "samachar/"},
            {"@type": "ListItem", "position": 3, "name": post.get("title"), "item": url},
        ],
    }
    return (json.dumps(article, ensure_ascii=False, separators=(",", ":")),
            json.dumps(breadcrumb, ensure_ascii=False, separators=(",", ":")))


def render_page(post, eligible, settings):
    slug = post["slug"]
    url = clean_url(slug)
    title = post.get("title") or "समाचार"
    desc = excerpt_of(post)
    img_abs = abs_img(post.get("image")) if post.get("image") else BASE + "images/og-image.jpg"
    logo = (settings or {}).get("logo") or "/images/logo_1_0.png"

    read_words = len(str(post.get("text") or "").split())
    read_min = max(1, round(read_words / 200))

    meta_line = " · ".join(esc(x) for x in [
        hindi_date(post.get("date")),
        (post.get("location") or "").strip(),
        post.get("category"),
        "%d मिनट पढ़ने का समय" % read_min,
    ] if x)
    if post.get("author"):
        meta_line += " · " + esc(post["author"])

    feature = ""
    if post.get("image"):
        feature = (
            '<img class="article-hero" src="%s" alt="%s" '
            'fetchpriority="high" width="1200" height="675" decoding="async" />'
        ) % (abs_img(post["image"]), esc(post.get("image_alt") or title))

    # Gallery
    gallery = ""
    gitems = post.get("gallery") or []
    if isinstance(gitems, list) and gitems:
        figs = []
        for g in gitems:
            src = g.get("src") if isinstance(g, dict) else g
            cap = g.get("caption") if isinstance(g, dict) else ""
            alt = ("संतोष सिकरवार - " + cap) if cap else "संतोष सिकरवार - कार्यक्रम फ़ोटो"
            figs.append(
                '<figure class="gallery-item" data-src="%s" data-caption="%s" '
                'tabindex="0" role="button" aria-label="%s">'
                '<img src="%s" alt="%s" loading="lazy" />%s</figure>'
                % (abs_img(src), esc(cap or ""), esc(cap or "फ़ोटो"),
                   abs_img(src), esc(alt),
                   ('<figcaption>%s</figcaption>' % esc(cap)) if cap else "")
            )
        gallery = '<div class="gallery-grid article-gallery">%s</div>' % "".join(figs)

    # Share bar
    from urllib.parse import quote
    enc = quote(url, safe="")
    enc_t = quote(title, safe="")
    share = (
        '<div class="share-bar" aria-label="साझा करें">'
        '<span class="share-label">साझा करें:</span>'
        '<a class="share-btn wa" href="https://wa.me/?text=%s%%20%s" target="_blank" rel="noopener">WhatsApp</a>'
        '<a class="share-btn fb" href="https://www.facebook.com/sharer/sharer.php?u=%s" target="_blank" rel="noopener">Facebook</a>'
        '<a class="share-btn xx" href="https://twitter.com/intent/tweet?text=%s&url=%s" target="_blank" rel="noopener">X</a>'
        '<button type="button" class="share-btn copy" id="share-copy">लिंक कॉपी</button>'
        '<button type="button" class="share-btn native" id="share-native" hidden>Share</button>'
        '</div>'
    ) % (enc_t, enc, enc, enc_t, enc)

    # Related
    rel = related_for(post, eligible)
    related_html = ""
    if rel:
        related_html = (
            '<section class="related"><h2 class="section-title" style="text-align:left">संबंधित गतिविधियाँ</h2>'
            '<div class="feed-grid">%s</div></section>'
        ) % "".join(render_card(p) for p in rel)

    article_ld, breadcrumb_ld = json_ld(post)

    return """<!DOCTYPE html>
<html lang="hi">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />

  <title>{title_esc} | Santosh Sikarwar</title>
  <meta name="description" content="{desc}" />
  <meta name="robots" content="index, follow, max-image-preview:large" />
  <meta name="referrer" content="strict-origin-when-cross-origin" />
  <meta name="theme-color" content="#f47216" />
  <link rel="canonical" href="{url}" />

  <link rel="icon" type="image/svg+xml" href="/images/bjp-lotus.svg" />
  <link rel="apple-touch-icon" href="/images/bjp-lotus.svg" />
  <link rel="manifest" href="/manifest.webmanifest" />

  <meta property="og:type" content="article" />
  <meta property="og:site_name" content="Santosh Sikarwar" />
  <meta property="og:title" content="{title_esc}" />
  <meta property="og:description" content="{desc}" />
  <meta property="og:url" content="{url}" />
  <meta property="og:image" content="{img_abs}" />
  <meta property="og:locale" content="hi_IN" />
  {article_time}
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{title_esc}" />
  <meta name="twitter:description" content="{desc}" />
  <meta name="twitter:image" content="{img_abs}" />

  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Devanagari:wght@400;500;600;700;800&family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="/styles.css?v=30" />

  <script type="application/ld+json">{article_ld}</script>
  <script type="application/ld+json">{breadcrumb_ld}</script>
</head>
<body>
  <a class="skip-link" href="#samachar-main">मुख्य सामग्री पर जाएँ</a>
  <div class="scroll-progress" id="scroll-progress" aria-hidden="true"></div>
  <div class="tricolor-strip"></div>

  <header class="site-header">
    <nav class="nav container" aria-label="मुख्य नेविगेशन">
      <a href="/" class="logo">
        <img class="lotus-logo" id="site-logo" src="{logo}" alt="भाजपा कमल" width="36" height="36" />
        <span class="logo-text">संतोष सिकरवार</span>
      </a>
      <button class="nav-toggle" aria-label="मेनू खोलें" aria-expanded="false">
        <span></span><span></span><span></span>
      </button>
      <ul class="nav-links">
        <li><a href="/">मुख्य पृष्ठ</a></li>
        <li><a href="/#about">परिचय</a></li>
        <li><a href="/samachar/">समाचार</a></li>
        <li><a href="/#gallery">गैलरी</a></li>
        <li><a href="/#contact">संपर्क</a></li>
      </ul>
    </nav>
  </header>

  <main id="samachar-main" class="section">
    <div class="container">
      <nav class="breadcrumb" aria-label="ब्रेडक्रम्ब">
        <a href="/">मुख्य पृष्ठ</a> <span>›</span> <a href="/samachar/">समाचार</a> <span>›</span> <span>{title_esc}</span>
      </nav>
      <div id="samachar-content">
        <article class="article">
          <h1>{title_esc}</h1>
          <p class="article-meta">{meta_line}</p>
          {share}
          {feature}
          <div class="article-body">{body}</div>
          {gallery}
          <p class="article-back"><a href="/samachar/">← समाचार सूची</a> · <a href="/">मुख्य पृष्ठ</a></p>
        </article>
        {related_html}
      </div>
    </div>
  </main>

  <footer class="site-footer">
    <div class="tricolor-strip"></div>
    <div class="container">
      <p class="footer-name">संतोष सिकरवार</p>
      <p class="footer-role">जिला उपाध्यक्ष, भारतीय जनता पार्टी, आगरा · आधिकारिक वेबसाइट</p>
      <nav class="footer-nav" aria-label="फ़ुटर नेविगेशन">
        <a href="/">मुख्य पृष्ठ</a>
        <a href="/#about">परिचय</a>
        <a href="/samachar/">समाचार</a>
        <a href="/#gallery">गैलरी</a>
        <a href="/#contact">संपर्क</a>
      </nav>
      <p class="footer-copy">&copy; <span id="year"></span> संतोष सिकरवार. सर्वाधिकार सुरक्षित.</p>
    </div>
  </footer>

  <button class="to-top" id="to-top" aria-label="ऊपर जाएँ" hidden>↑</button>

  <div id="lightbox" class="lightbox" aria-hidden="true">
    <button class="lightbox-close" aria-label="बंद करें">&times;</button>
    <button class="lightbox-nav lightbox-prev" id="lightbox-prev" aria-label="पिछली फ़ोटो" hidden>‹</button>
    <img src="" alt="" id="lightbox-img" />
    <button class="lightbox-nav lightbox-next" id="lightbox-next" aria-label="अगली फ़ोटो" hidden>›</button>
    <p id="lightbox-caption"></p>
    <span class="lightbox-counter" id="lightbox-counter" hidden></span>
  </div>

  <script src="/samachar/article.js?v=1"></script>
</body>
</html>
""".format(
        title_esc=esc(title),
        desc=esc(desc),
        url=url,
        img_abs=img_abs,
        logo=esc(logo),
        article_time=(('<meta property="article:published_time" content="%s" />'
                       % esc(post["date"])) if post.get("date") else ""),
        article_ld=article_ld,
        breadcrumb_ld=breadcrumb_ld,
        meta_line=meta_line,
        share=share,
        feature=feature,
        body=body_html(post.get("text")),
        gallery=gallery,
        related_html=related_html,
    )


# ---------- output ----------
def write_or_check(path, content, check_only):
    rel = os.path.relpath(path, ROOT)
    old = None
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8", newline="") as fh:
            old = fh.read()
    changed = old != content
    if check_only:
        if changed:
            print("  %-55s %s" % (rel, "WOULD CHANGE" if old is not None else "WOULD CREATE"))
        return changed
    if changed:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(content)
        print("  %-55s %s" % (rel, "written (changed)" if old is not None else "created"))
    return changed


def cleanup_stale(valid_slugs, check_only):
    """Remove samachar/<slug>/ folders that are no longer published."""
    removed = []
    if not os.path.isdir(SAMACHAR_DIR):
        return removed
    for name in sorted(os.listdir(SAMACHAR_DIR)):
        sub = os.path.join(SAMACHAR_DIR, name)
        if not os.path.isdir(sub):
            continue
        # Only touch folders that look like generated article pages
        if not SLUG_RE.match(name):
            continue
        if name in valid_slugs:
            continue
        removed.append(name)
        if not check_only:
            shutil.rmtree(sub)
            print("  removed stale: samachar/%s/" % name)
        else:
            print("  %-55s WOULD REMOVE" % ("samachar/%s/" % name))
    return removed


def main():
    ap = argparse.ArgumentParser(description="Pre-render static article pages from data/feed.json")
    ap.add_argument("--check", action="store_true", help="Report changes without writing")
    args = ap.parse_args()

    feed = load_json(FEED_PATH)
    if feed is None:
        print("ERROR: data/feed.json not found")
        sys.exit(1)
    settings = load_json(SETTINGS_PATH) or {}

    published = published_posts(feed)
    eligible = eligible_posts(published)
    valid_slugs = {p["slug"] for (_, p) in eligible}

    total = len(feed.get("posts", []) if isinstance(feed, dict) else [])
    print("Source : data/feed.json (%d total / %d published / %d with valid unique slug)"
          % (total, len(published), len(eligible)))
    print("Pages:")

    changed = False
    for _, post in eligible:
        path = os.path.join(SAMACHAR_DIR, post["slug"], "index.html")
        changed |= write_or_check(path, render_page(post, eligible, settings), args.check)

    stale = cleanup_stale(valid_slugs, args.check)
    changed = changed or bool(stale)

    if WARNINGS:
        print("\nWarnings (%d):" % len(WARNINGS))
        for w in WARNINGS:
            print("  ! " + w)
    else:
        print("\nNo warnings.")

    if args.check:
        print("\nCheck mode: no files were written.")
        sys.exit(1 if changed else 0)
    print("\nDone. %d article pages are current." % len(eligible))


if __name__ == "__main__":
    main()
