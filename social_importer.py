#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
social_importer.py
====================================================================
Import posts from Twitter / X (@ssikarwarbjp) and Facebook,
format them for the website feed, pre-render static pages, and
push live to GitHub.
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.parse
from datetime import datetime, date

# Import helpers from existing project scripts
from new_post import (
    ROOT,
    FEED_PATH,
    AUTHOR,
    make_title,
    make_slug,
    make_excerpt,
    categorize,
    _strip_noise,
)
from build_static_pages import main as run_build_static_pages


def log(msg):
    print(f"[Social Sync] {msg}")


def download_image(img_url, dest_name):
    """Download an image from a URL and save into images/ folder."""
    images_dir = os.path.join(ROOT, "images")
    os.makedirs(images_dir, exist_ok=True)
    filename = f"social_{dest_name[:40]}.jpg"
    dest_path = os.path.join(images_dir, filename)

    try:
        req = urllib.request.Request(
            img_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
        )
        with urllib.request.urlopen(req, timeout=15) as resp, open(dest_path, "wb") as out:
            out.write(resp.read())
        log(f"Saved image to images/{filename}")
        return f"/images/{filename}"
    except Exception as e:
        log(f"Warning: Could not download image ({e})")
        return ""


def fetch_twitter_post(url_or_id):
    """Fetch post details from Twitter / X using the official syndication endpoint."""
    tweet_id_match = re.search(r"(?:status|statuses)/(\d+)", str(url_or_id))
    tweet_id = tweet_id_match.group(1) if tweet_id_match else str(url_or_id).strip()

    if not tweet_id.isdigit():
        raise ValueError(f"Invalid Tweet ID or URL: {url_or_id}")

    endpoint = f"https://cdn.syndication.twimg.com/tweet-result?id={tweet_id}&token=x"
    req = urllib.request.Request(
        endpoint,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        raise RuntimeError(f"Failed to fetch Tweet {tweet_id}: {e}")

    text = data.get("text", "")
    created_at_raw = data.get("created_at", "")
    post_date = date.today().isoformat()
    if created_at_raw:
        try:
            # Parse Twitter date format: "Wed Oct 14 12:00:00 +0000 2026"
            dt = datetime.strptime(created_at_raw, "%a %b %d %H:%M:%S %z %Y")
            post_date = dt.strftime("%Y-%m-%d")
        except Exception:
            pass

    # Extract photos
    photos = []
    if "photos" in data and isinstance(data["photos"], list):
        for p in data["photos"]:
            if "url" in p:
                photos.append(p["url"])
    elif "mediaDetails" in data and isinstance(data["mediaDetails"], list):
        for m in data["mediaDetails"]:
            if m.get("type") == "photo" and "media_url_https" in m:
                photos.append(m["media_url_https"])

    canonical_url = f"https://x.com/ssikarwarbjp/status/{tweet_id}"
    return {
        "platform": "twitter",
        "url": canonical_url,
        "text": text,
        "date": post_date,
        "photos": photos,
    }


def fetch_facebook_post(url):
    """Fetch post details from Facebook using system Chrome via Playwright or fallback metadata."""
    log(f"Fetching Facebook post: {url}")
    from playwright.sync_api import sync_playwright

    text = ""
    photos = []
    post_date = date.today().isoformat()

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=25000)
            page.wait_for_timeout(3000)

            # Try Open Graph meta tags first
            og_desc = page.locator('meta[property="og:description"]').get_attribute("content")
            og_img = page.locator('meta[property="og:image"]').get_attribute("content")

            if og_desc:
                text = og_desc
            if og_img and not og_img.endswith("rsrc.php"):
                photos.append(og_img)

            # Try page DOM selectors
            if not text:
                text_candidates = page.locator('[data-ad-preview="message"], [dir="auto"]').all_text_contents()
                for t in text_candidates:
                    if len(t.strip()) > 30 and not any(k in t for k in ["Log In", "Facebook", "Sign Up"]):
                        text = t.strip()
                        break

            # Try finding images in the post container
            img_elems = page.locator('div[role="feed"] img, [role="main"] img').all()
            for img in img_elems:
                src = img.get_attribute("src")
                if src and src.startswith("http") and not any(k in src for k in ["static", "rsrc.php", "emoji"]):
                    if src not in photos:
                        photos.append(src)

        except Exception as e:
            log(f"Warning during Facebook page scan: {e}")
        finally:
            browser.close()

    return {
        "platform": "facebook",
        "url": url,
        "text": text,
        "date": post_date,
        "photos": photos,
    }


def add_post_to_feed(item, location="आगरा, उत्तर प्रदेश"):
    """Format and save imported post into data/feed.json."""
    raw_text = item.get("text") or ""
    if not raw_text.strip():
        raise ValueError("Could not extract any text from this post.")

    # Load existing feed
    with open(FEED_PATH, "r", encoding="utf-8") as fh:
        feed = json.load(fh)

    existing_slugs = {p.get("slug") for p in feed.get("posts", []) if p.get("slug")}

    # Check for duplicate
    post_url = item.get("url")
    for p in feed.get("posts", []):
        if p.get("source", {}).get("url") == post_url:
            log(f"Post already imported previously as slug: '{p.get('slug')}'")
            return p

    title = make_title(raw_text)
    if not title:
        title = f"संतोष सिकरवार - {item.get('date')}"

    slug = make_slug(title, existing_slugs)
    excerpt = make_excerpt(raw_text)
    category = categorize(raw_text)

    # Download featured image and gallery
    featured_img_path = ""
    gallery = []
    photos = item.get("photos", [])

    if photos:
        featured_img_path = download_image(photos[0], f"{slug}_feat")
        for i, extra_url in enumerate(photos[1:], start=1):
            extra_path = download_image(extra_url, f"{slug}_gal_{i}")
            if extra_path:
                gallery.append({"src": extra_path, "caption": title})

    new_post = {
        "title": title,
        "slug": slug,
        "date": item.get("date") or date.today().isoformat(),
        "location": location,
        "category": category,
        "image": featured_img_path,
        "image_alt": title,
        "excerpt": excerpt,
        "text": raw_text,
        "gallery": gallery,
        "author": AUTHOR,
        "featured": False,
        "published": True,
        "updated_at": "",
        "source": {
            "platform": item.get("platform", "social"),
            "url": post_url,
            "imported_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
    }

    # Prepend new post
    feed["posts"].insert(0, new_post)

    with open(FEED_PATH, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(feed, fh, ensure_ascii=False, indent=2)

    log(f"Successfully added post: '{title}' (slug: {slug})")
    return new_post


def git_publish(commit_title):
    """Git commit and push changes live to GitHub repository."""
    log("Committing changes and pushing to GitHub...")
    import subprocess
    try:
        subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
        subprocess.run(
            ["git", "commit", "-m", f"Import social post: {commit_title}"],
            cwd=ROOT,
            check=True
        )
        subprocess.run(["git", "push", "origin", "main"], cwd=ROOT, check=True)
        log("Published live to GitHub successfully!")
    except subprocess.CalledProcessError as e:
        log(f"Git push warning: {e}")


def process_url(url, push_live=True):
    """Import, format, build static pages, and push live."""
    url = url.strip()
    if not url:
        return

    log(f"Processing URL: {url}")
    if "twitter.com" in url or "x.com" in url:
        item = fetch_twitter_post(url)
    elif "facebook.com" in url or "fb.watch" in url:
        item = fetch_facebook_post(url)
    else:
        raise ValueError(f"Unrecognized social platform URL: {url}")

    post = add_post_to_feed(item)

    # Re-build static pages & sitemaps
    log("Rebuilding static pages & sitemaps...")
    run_build_static_pages()

    if push_live:
        git_publish(post["title"])

    print("\n" + "=" * 60)
    print(f"DONE! Article is LIVE at:")
    print(f"  https://santoshsikarwar.in/samachar/{post['slug']}/")
    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Import social media posts to santoshsikarwar.in")
    parser.add_argument("--url", help="Twitter (X) or Facebook post URL")
    parser.add_argument("--no-push", action="store_true", help="Do not git push after building")
    args = parser.parse_args()

    url = args.url
    if not url:
        print("=" * 60)
        print("  Santosh Sikarwar Website - Social Media Importer")
        print("=" * 60)
        url = input("\nPaste Twitter (X) or Facebook post URL: ").strip()

    if url:
        process_url(url, push_live=not args.no_push)


if __name__ == "__main__":
    main()
