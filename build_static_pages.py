#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_static_pages.py
====================================================================
Static Site Generator for https://santoshsikarwar.in/

Pre-renders all news articles from data/feed.json into clean static
HTML pages under samachar/<slug>/index.html.
Also pre-renders latest articles into index.html for instant Google crawling.
Finally, regenerates sitemap.xml and image-sitemap.xml.
"""

import html
import json
import os
import re
import sys
from datetime import date
from generate_sitemaps import (
    BASE,
    ROOT,
    FEED_PATH,
    SETTINGS_PATH,
    load_json,
    valid_date,
    published_posts,
    eligible_posts,
    build_sitemap,
    build_image_sitemap,
    build_news_sitemap,
    write_or_check,
)

HINDI_MONTHS = [
    "जनवरी", "फ़रवरी", "मार्च", "अप्रैल", "मई", "जून",
    "जुलाई", "अगस्त", "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर"
]

def format_hindi_date(d):
    if not d:
        return ""
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", str(d))
    if m:
        year, month, day = m.groups()
        return f"{int(day)} {HINDI_MONTHS[int(month) - 1]} {year}"
    return str(d)

def abs_img(v):
    if not v:
        return ""
    if v.startswith("http://") or v.startswith("https://"):
        return v
    if v.startswith("/"):
        return v
    clean = re.sub(r"^/?images/", "", v)
    return "/images/" + clean

def post_excerpt(post):
    if post.get("excerpt"):
        return post["excerpt"].strip()
    t = re.sub(r"\s+", " ", post.get("text") or "").strip()
    return (t[:160] + "…") if len(t) > 160 else t

def body_to_html(text):
    if not text:
        return ""
    paras = re.split(r"\n{2,}", text)
    out = []
    for p in paras:
        p_clean = p.strip()
        if not p_clean:
            continue
        p_esc = html.escape(p_clean).replace("\n", "<br>")
        out.append(f"<p>{p_esc}</p>")
    return "\n      ".join(out)

def render_card(post, idx):
    slug = post.get("slug")
    href = f"/samachar/{slug}/" if slug else f"/samachar/?id={idx}"
    title_esc = html.escape(post.get("title") or "")
    alt_esc = html.escape(post.get("image_alt") or post.get("title") or "")
    excerpt_esc = html.escape(post_excerpt(post))
    
    img_tag = ""
    if post.get("image"):
        img_src = abs_img(post["image"])
        img_tag = f'<div class="feed-img"><img src="{img_src}" alt="{alt_esc}" loading="lazy" /></div>'
    
    meta_parts = [p for p in [post.get("category"), post.get("location")] if p]
    meta_str = " · ".join(html.escape(p) for p in meta_parts)
    meta_tag = f'<span class="feed-meta">{meta_str}</span>' if meta_str else ""
    date_str = format_hindi_date(post.get("date"))

    return f"""    <a class="feed-card" href="{href}" aria-label="{title_esc}">
      {img_tag}
      <div class="feed-body">
        <span class="feed-date">{date_str}</span>
        {meta_tag}
        <h3>{title_esc}</h3>
        <p>{excerpt_esc}</p>
        <span class="read-more">और पढ़ें →</span>
      </div>
    </a>"""

def generate_article_page(post, idx, all_eligible):
    slug = post["slug"]
    title = post.get("title") or ""
    title_esc = html.escape(title)
    desc = post_excerpt(post)
    desc_esc = html.escape(desc)
    canonical_url = f"{BASE}samachar/{slug}/"
    
    # Image
    img_rel = abs_img(post.get("image") or "/images/og-image.jpg")
    img_abs = img_rel if img_rel.startswith("http") else (BASE.rstrip("/") + img_rel)
    alt_esc = html.escape(post.get("image_alt") or title)

    # Word count & reading time
    words = len(re.findall(r"\S+", post.get("text") or ""))
    read_min = max(1, round(words / 200))

    # Meta line
    meta_parts = [format_hindi_date(post.get("date")), post.get("location"), post.get("category"), f"{read_min} मिनट पढ़ने का समय"]
    meta_line = " · ".join(html.escape(p) for p in meta_parts if p)
    author = html.escape(post.get("author") or "संतोष सिकरवार")

    # Share URLs
    from urllib.parse import quote
    enc_u = quote(canonical_url, safe="")
    enc_t = quote(title, safe="")

    # Hero image
    feature_html = ""
    if post.get("image"):
        feature_html = f'<img class="article-hero" src="{abs_img(post["image"])}" alt="{alt_esc}" fetchpriority="high" width="1200" height="675" decoding="async" />'

    # Body
    body_html = body_to_html(post.get("text") or "")

    # Gallery
    gallery_html = ""
    gallery = post.get("gallery") or []
    if isinstance(gallery, list) and gallery:
        items = []
        for g in gallery:
            src = g.get("src") if isinstance(g, dict) else g
            cap = (g.get("caption") if isinstance(g, dict) else "") or ""
            cap_esc = html.escape(cap)
            g_alt = html.escape(f"संतोष सिकरवार - {cap}" if cap else "संतोष सिकरवार - कार्यक्रम फ़ोटो")
            g_src = abs_img(src)
            items.append(f"""        <figure class="gallery-item" data-src="{g_src}" data-caption="{cap_esc}" tabindex="0" role="button" aria-label="{cap_esc or 'फ़ोटो'}">
          <img src="{g_src}" alt="{g_alt}" loading="lazy" />
          {f'<figcaption>{cap_esc}</figcaption>' if cap else ''}
        </figure>""")
        gallery_html = '<div class="gallery-grid article-gallery">\n' + "\n".join(items) + '\n      </div>'

    # Related posts (up to 3)
    related = [p for p in all_eligible if p[0] != idx]
    related.sort(
        key=lambda ip: (
            0 if ip[1].get("category") == post.get("category") else 1,
            ip[1].get("date") or ""
        ),
        reverse=True
    )
    related = related[:3]
    related_html = ""
    if related:
        cards = "\n".join(render_card(p, i) for i, p in related)
        related_html = f"""      <section class="related">
        <h2 class="section-title" style="text-align:left">संबंधित गतिविधियाँ</h2>
        <div class="feed-grid">
{cards}
        </div>
      </section>"""

    # Schema JSON-LD
    schema_ld = {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": title,
        "description": desc,
        "image": [img_abs],
        "datePublished": post.get("date") or date.today().isoformat(),
        "dateModified": post.get("updated_at") or post.get("date") or date.today().isoformat(),
        "articleSection": post.get("category") or "समाचार",
        "inLanguage": "hi-IN",
        "author": {"@type": "Person", "name": post.get("author") or "संतोष सिकरवार"},
        "publisher": {
            "@type": "Organization",
            "name": "Santosh Sikarwar",
            "logo": {"@type": "ImageObject", "url": BASE + "images/santosh-sikarwar.jpg"}
        },
        "about": {"@type": "Person", "@id": BASE + "#person", "name": "Santosh Sikarwar"},
        "mainEntityOfPage": {"@type": "WebPage", "@id": canonical_url}
    }
    schema_json = json.dumps(schema_ld, ensure_ascii=False, indent=2)

    html_content = f"""<!DOCTYPE html>
<html lang="hi">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />

  <!-- Pre-rendered SEO for Googlebot & Users -->
  <title>{title_esc} | Santosh Sikarwar</title>
  <meta name="description" content="{desc_esc}" />
  <meta name="robots" content="index, follow, max-image-preview:large" id="meta-robots" />
  <meta name="referrer" content="strict-origin-when-cross-origin" />
  <meta name="theme-color" content="#f47216" />
  <link rel="canonical" href="{canonical_url}" id="canonical-link" />

  <link rel="icon" type="image/svg+xml" href="/images/bjp-lotus.svg" />
  <link rel="apple-touch-icon" href="/images/bjp-lotus.svg" />
  <link rel="manifest" href="/manifest.webmanifest" />

  <!-- Open Graph -->
  <meta property="og:type" content="article" id="og-type" />
  <meta property="og:site_name" content="Santosh Sikarwar" />
  <meta property="og:title" content="{title_esc}" id="og-title" />
  <meta property="og:description" content="{desc_esc}" id="og-desc" />
  <meta property="og:url" content="{canonical_url}" id="og-url" />
  <meta property="og:image" content="{img_abs}" id="og-image" />

  <!-- Twitter / X Card -->
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{title_esc}" id="tw-title" />
  <meta name="twitter:description" content="{desc_esc}" id="tw-desc" />
  <meta name="twitter:image" content="{img_abs}" id="tw-image" />

  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Devanagari:wght@400;500;600;700;800&family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="/styles.css?v=31" />

  <!-- Schema.org NewsArticle Structured Data -->
  <script type="application/ld+json" id="article-jsonld">
{schema_json}
  </script>
</head>
<body>
  <a class="skip-link" href="#samachar-main">मुख्य सामग्री पर जाएँ</a>
  <div class="scroll-progress" id="scroll-progress" aria-hidden="true"></div>
  <div class="tricolor-strip"></div>

  <header class="site-header">
    <nav class="nav container" aria-label="मुख्य नेविगेशन">
      <a href="/" class="logo">
        <img class="lotus-logo" id="site-logo" src="/images/logo_1_0.png" alt="भाजपा कमल" width="36" height="36" />
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
      <nav class="breadcrumb" id="breadcrumb" aria-label="ब्रेडक्रम्ब">
        <a href="/">मुख्य पृष्ठ</a> <span>›</span> <a href="/samachar/">समाचार</a> <span>›</span> <span>{title_esc}</span>
      </nav>
      <div id="samachar-content">
        <article class="article">
          <h1>{title_esc}</h1>
          <p class="article-meta">{meta_line} · {author}</p>
          <div class="share-bar" aria-label="साझा करें">
            <span class="share-label">साझा करें:</span>
            <a class="share-btn wa" href="https://wa.me/?text={enc_t}%20{enc_u}" target="_blank" rel="noopener">WhatsApp</a>
            <a class="share-btn fb" href="https://www.facebook.com/sharer/sharer.php?u={enc_u}" target="_blank" rel="noopener">Facebook</a>
            <a class="share-btn xx" href="https://twitter.com/intent/tweet?text={enc_t}&amp;url={enc_u}" target="_blank" rel="noopener">X</a>
            <button type="button" class="share-btn copy" id="share-copy">लिंक कॉपी</button>
            <button type="button" class="share-btn native" id="share-native" hidden>Share</button>
          </div>
          {feature_html}
          <div class="article-body">
            {body_html}
          </div>
          {gallery_html}
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

  <script src="/samachar/samachar.js?v=11"></script>
</body>
</html>
"""
    article_dir = os.path.join(ROOT, "samachar", slug)
    os.makedirs(article_dir, exist_ok=True)
    out_path = os.path.join(article_dir, "index.html")
    with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(html_content)
    return out_path


def pre_render_homepage_feed(eligible):
    index_path = os.path.join(ROOT, "index.html")
    if not os.path.isfile(index_path):
        return
    with open(index_path, "r", encoding="utf-8") as fh:
        content = fh.read()

    # Pre-render top 6 articles
    top6 = eligible[:6]
    cards_html = "\n".join(render_card(post, idx) for idx, post in top6)
    pattern = re.compile(
        r'(<div id="feed-grid" class="feed-grid">)(.*?)(</div>\s*<div class="feed-more">)',
        flags=re.DOTALL
    )
    replacement = r'\1\n' + cards_html + r'\n        \3'
    if pattern.search(content):
        new_content = pattern.sub(replacement, content)
        with open(index_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(new_content)
        print("  index.html: Pre-rendered top 6 news articles into feed-grid")


def main():
    feed = load_json(FEED_PATH)
    if not feed:
        print("ERROR: data/feed.json missing")
        sys.exit(1)
    
    settings = load_json(SETTINGS_PATH) or {}
    published = published_posts(feed)
    eligible = eligible_posts(published)

    print(f"Pre-rendering {len(eligible)} news articles into static HTML pages...")
    for idx, post in eligible:
        p = generate_article_page(post, idx, eligible)
        print(f"  samachar/{post['slug']}/index.html created")

    pre_render_homepage_feed(eligible)

    # Now regenerate sitemaps
    print("\nRegenerating sitemaps with clean static URLs...")
    write_or_check("sitemap.xml", build_sitemap(eligible), False)
    write_or_check("image-sitemap.xml", build_image_sitemap(eligible, settings), False)
    write_or_check("news-sitemap.xml", build_news_sitemap(eligible, date.today()), False)
    print("\nDone! All articles are now pre-rendered static HTML with full SEO tags.")


if __name__ == "__main__":
    main()
