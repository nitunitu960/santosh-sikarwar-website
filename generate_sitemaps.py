#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_sitemaps.py
====================================================================
Deterministic sitemap generator for https://santoshsikarwar.in/

Single source of truth : data/feed.json  (+ data/settings.json for the
                         homepage hero image only)
Generates              : sitemap.xml, image-sitemap.xml, news-sitemap.xml

Design rules
--------------------------------------------------------------------
* Uses ONLY published content (published != false).
* Deterministic: the same feed.json produces byte-identical XML on a
  given day. No generation timestamps are embedded anywhere; article
  <lastmod> values come from the feed data itself (updated_at or date).
* News sitemap: only articles whose ORIGINAL publication date is within
  the previous 2 days (Google News guidance). updated_at is never used
  to make an old article look new. If none qualify, a valid EMPTY
  urlset is written.
* It never modifies Decap CMS config, feed.json, the admin panel,
  article rendering, or existing article URLs. It only reads JSON and
  writes the three XML files.

Usage
--------------------------------------------------------------------
    python generate_sitemaps.py
    python generate_sitemaps.py --today 2026-08-16   # testing the news window
    python generate_sitemaps.py --check              # report only, do not write
"""

import argparse
import json
import os
import re
import sys
from datetime import date, timedelta

BASE = "https://santoshsikarwar.in/"
ROOT = os.path.dirname(os.path.abspath(__file__))
FEED_PATH = os.path.join(ROOT, "data", "feed.json")
SETTINGS_PATH = os.path.join(ROOT, "data", "settings.json")

# Static canonical documents: (path, changefreq, priority)
STATIC_URLS = [
    ("", "weekly", "1.0"),
    ("samachar/", "weekly", "0.8"),
    ("privacy-policy.html", "yearly", "0.3"),
    ("terms.html", "yearly", "0.3"),
    ("disclaimer.html", "yearly", "0.3"),
]

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

WARNINGS = []


def warn(msg):
    WARNINGS.append(msg)


# ---------- helpers ----------
def xml_escape(value):
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
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


def valid_date(value):
    """Return a date object if value is a valid YYYY-MM-DD string, else None."""
    if not isinstance(value, str) or not DATE_RE.match(value):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def norm_image(value):
    """Normalise a feed image path to 'images/xxx' or None if unusable."""
    if not value or not isinstance(value, str):
        return None
    rel = value.strip().lstrip("/")
    if not rel:
        return None
    if not rel.startswith("images/"):
        rel = "images/" + rel
    return rel


def image_exists(rel):
    return os.path.isfile(os.path.join(ROOT, rel.replace("/", os.sep)))


def image_abs(rel):
    return BASE + rel


def article_url(post):
    """Canonical article URL (slug-based only). Caller must pass a slug-eligible post."""
    return BASE + "samachar/?slug=" + post["slug"]


def published_posts(feed):
    """(original_index, post) for published posts, sorted date desc then slug."""
    posts = feed.get("posts", []) if isinstance(feed, dict) else []
    out = [(i, p) for i, p in enumerate(posts) if p.get("published") is not False]
    out.sort(key=lambda ip: (ip[1].get("date") or "", ip[1].get("slug") or ""), reverse=True)
    return out


def eligible_posts(published):
    """Published posts that may appear in sitemaps: those with a VALID, UNIQUE slug.
    Missing / invalid / duplicate slug -> warn and EXCLUDE from all sitemaps.
    No ?id= fallback is ever generated (a sitemap must contain only canonical URLs)."""
    eligible = []
    seen = {}
    for idx, post in published:
        title = str(post.get("title") or "")[:40]
        slug = post.get("slug")
        if not slug:
            warn("post #%d ('%s'): missing slug -> EXCLUDED from all sitemaps "
                 "(add a lowercase-hyphen slug to include it)" % (idx, title))
            continue
        if not SLUG_RE.match(slug):
            warn("post #%d ('%s'): invalid slug '%s' -> EXCLUDED from all sitemaps "
                 "(use lowercase letters, digits and hyphens)" % (idx, title, slug))
            continue
        if slug in seen:
            warn("post #%d ('%s'): duplicate slug '%s' (first used by post #%d) "
                 "-> duplicate EXCLUDED from all sitemaps" % (idx, title, slug, seen[slug]))
            continue
        seen[slug] = idx
        eligible.append((idx, post))
    return eligible


# ---------- validation ----------
def validate(published):
    """Warn about missing title/date and missing image files.
    (Slug validity + uniqueness is handled by eligible_posts, which excludes
    offending articles from every sitemap.)"""
    for idx, post in published:
        title = post.get("title")
        if not title or not str(title).strip():
            warn("post #%d: missing title" % idx)

        if valid_date(post.get("date")) is None:
            warn("post #%d ('%s'): missing/invalid date '%s' (expected YYYY-MM-DD)"
                 % (idx, str(title)[:40], post.get("date")))

        # image existence checks (broken/placeholder paths are skipped later)
        feat = norm_image(post.get("image"))
        if feat and not image_exists(feat):
            warn("post #%d: featured image not found in repo, skipped: %s" % (idx, feat))
        for g in post.get("gallery") or []:
            gi = norm_image(g.get("src") if isinstance(g, dict) else g)
            if gi and not image_exists(gi):
                warn("post #%d: gallery image not found in repo, skipped: %s" % (idx, gi))


# ---------- builders ----------
def build_sitemap(eligible):
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path, changefreq, priority in STATIC_URLS:
        lines += ["  <url>",
                  "    <loc>%s%s</loc>" % (BASE, path),
                  "    <changefreq>%s</changefreq>" % changefreq,
                  "    <priority>%s</priority>" % priority,
                  "  </url>"]
    emitted = set()
    for idx, post in eligible:
        url = article_url(post)
        if url in emitted:
            continue
        emitted.add(url)
        lastmod = valid_date(post.get("updated_at")) or valid_date(post.get("date"))
        lines.append("  <url>")
        lines.append("    <loc>%s</loc>" % xml_escape(url))
        if lastmod:
            lines.append("    <lastmod>%s</lastmod>" % lastmod.isoformat())
        lines += ["    <changefreq>monthly</changefreq>",
                  "    <priority>0.6</priority>",
                  "  </url>"]
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def build_image_sitemap(eligible, settings):
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
             '        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">']

    # Homepage images (hero photo from settings + person portrait), only if present
    home_imgs = []
    hero = norm_image((settings or {}).get("photo"))
    if hero and image_exists(hero):
        home_imgs.append((hero, "Santosh Sikarwar, District Vice President, BJP Agra"))
    portrait = "images/santosh-sikarwar.jpg"
    if image_exists(portrait):
        home_imgs.append((portrait, "Santosh Sikarwar"))
    # National Spirit section photo (homepage), only if the file exists
    for rel, title in (
        ("images/national-spirit-2.jpg", "Santosh Sikarwar with the Indian national flag"),
    ):
        if image_exists(rel):
            home_imgs.append((rel, title))
    if home_imgs:
        lines.append("  <!-- Homepage images -->")
        lines.append("  <url>")
        lines.append("    <loc>%s</loc>" % BASE)
        for rel, title in home_imgs:
            lines += ["    <image:image>",
                      "      <image:loc>%s</image:loc>" % xml_escape(image_abs(rel)),
                      "      <image:title>%s</image:title>" % xml_escape(title),
                      "    </image:image>"]
        lines.append("  </url>")

    # Article images (featured + gallery), mapped to the article's own page
    for idx, post in eligible:
        imgs = []
        feat = norm_image(post.get("image"))
        if feat and image_exists(feat):
            imgs.append((feat, post.get("image_alt") or post.get("title") or "Santosh Sikarwar"))
        for g in post.get("gallery") or []:
            src = g.get("src") if isinstance(g, dict) else g
            cap = g.get("caption") if isinstance(g, dict) else None
            gi = norm_image(src)
            if gi and image_exists(gi) and gi not in [x[0] for x in imgs]:
                imgs.append((gi, cap or post.get("title") or "Santosh Sikarwar"))
        if not imgs:
            continue
        lines.append("  <url>")
        lines.append("    <loc>%s</loc>" % xml_escape(article_url(post)))
        for rel, title in imgs:
            lines += ["    <image:image>",
                      "      <image:loc>%s</image:loc>" % xml_escape(image_abs(rel)),
                      "      <image:title>%s</image:title>" % xml_escape(title),
                      "    </image:image>"]
        lines.append("  </url>")

    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def build_news_sitemap(eligible, today):
    recent = []
    for idx, post in eligible:
        pub = valid_date(post.get("date"))
        if pub is None:
            continue
        delta = (today - pub).days
        if 0 <= delta <= 2:                     # within the previous 2 days only
            recent.append((idx, post, pub))

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<!--',
             '  Google News sitemap. Contains ONLY genuine articles published in the',
             '  last 2 days. Regenerated by generate_sitemaps.py; do not edit by hand.',
             '  Effective only if Google accepts the site as a News source.',
             '-->',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
             '        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">']
    for idx, post, pub in recent:
        lines += ["  <url>",
                  "    <loc>%s</loc>" % xml_escape(article_url(post)),
                  "    <news:news>",
                  "      <news:publication>",
                  "        <news:name>Santosh Sikarwar</news:name>",
                  "        <news:language>hi</news:language>",
                  "      </news:publication>",
                  "      <news:publication_date>%s</news:publication_date>" % pub.isoformat(),
                  "      <news:title>%s</news:title>" % xml_escape(post.get("title") or ""),
                  "    </news:news>",
                  "  </url>"]
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


# ---------- output ----------
def write_or_check(filename, content, check_only):
    path = os.path.join(ROOT, filename)
    old = None
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8", newline="") as fh:
            old = fh.read()
    changed = old != content
    if check_only:
        print("  %-20s %s" % (filename, "WOULD CHANGE" if changed else "unchanged"))
        return changed
    if changed:
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(content)
        print("  %-20s %s" % (filename, "written (changed)" if old is not None else "created"))
    else:
        print("  %-20s unchanged" % filename)
    return changed


def main():
    ap = argparse.ArgumentParser(description="Generate sitemaps from data/feed.json")
    ap.add_argument("--today", help="Override today's date (YYYY-MM-DD); news-window testing only")
    ap.add_argument("--check", action="store_true", help="Report changes without writing files")
    args = ap.parse_args()

    if not BASE.startswith("https://"):
        print("ERROR: BASE must be an absolute HTTPS URL")
        sys.exit(1)

    today = valid_date(args.today) if args.today else date.today()
    if args.today and today is None:
        print("ERROR: --today must be YYYY-MM-DD")
        sys.exit(1)

    feed = load_json(FEED_PATH)
    if feed is None:
        print("ERROR: data/feed.json not found")
        sys.exit(1)
    settings = load_json(SETTINGS_PATH) or {}

    published = published_posts(feed)
    validate(published)
    eligible = eligible_posts(published)

    total = len(feed.get("posts", []) if isinstance(feed, dict) else [])
    print("Source     : data/feed.json (%d total / %d published / %d with a valid unique slug)"
          % (total, len(published), len(eligible)))
    print("News window : articles dated %s .. %s"
          % ((today - timedelta(days=2)).isoformat(), today.isoformat()))
    print("Files:")

    changed = False
    changed |= write_or_check("sitemap.xml", build_sitemap(eligible), args.check)
    changed |= write_or_check("image-sitemap.xml", build_image_sitemap(eligible, settings), args.check)
    changed |= write_or_check("news-sitemap.xml", build_news_sitemap(eligible, today), args.check)

    if WARNINGS:
        print("\nWarnings (%d):" % len(WARNINGS))
        for w in WARNINGS:
            print("  ! " + w)
    else:
        print("\nNo warnings.")

    if args.check:
        print("\nCheck mode: no files were written.")
        sys.exit(1 if changed else 0)
    print("\nDone. Review the files and `git diff`, then commit & push.")


if __name__ == "__main__":
    main()
