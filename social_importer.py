#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
social_importer.py
====================================================================
Import posts from Twitter / X (@ssikarwarbjp, @BJP4UP, etc.) and Facebook,
automatically expand short/thin posts using Gemini AI into
rich 300+ word articles (Google Search Console compliant),
pre-render static HTML pages, and push live to GitHub.

Supports:
- Specific Tweet URLs: https://x.com/username/status/123456...
- Twitter Profile URLs: https://x.com/BJP4UP (fetches latest tweet)
- Specific Facebook Post URLs: https://www.facebook.com/user/posts/123...
- Facebook Page URLs: https://www.facebook.com/Santoshsikarwarbjpagra/ (fetches latest post)
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.parse
from datetime import datetime, date, timezone

# Set UTF-8 encoding for standard output
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

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


def get_gemini_api_key():
    """Retrieve Gemini API key from environment or gemini_config.json."""
    env_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if env_key:
        return env_key

    candidates = [
        os.path.join(ROOT, "gemini_config.json"),
        os.path.join(os.path.dirname(ROOT), "gemini_config.json"),
    ]
    for p in candidates:
        if os.path.isfile(p):
            try:
                with open(p, "r", encoding="utf-8") as fh:
                    cfg = json.load(fh)
                    k = cfg.get("gemini_api_key", "").strip()
                    if k:
                        return k
            except Exception:
                pass
    return ""


def expand_with_gemini(raw_text, post_date=""):
    """
    Expands short social post into a substantial 300+ word article
    compliant with Google Search Console quality guidelines (no thin content).
    Returns dict(title=..., text=..., category=..., location=...) or None.
    """
    api_key = get_gemini_api_key()
    if not api_key:
        log("No Gemini API key found, skipping AI expansion.")
        return None

    prompt = f"""You are an expert Hindi political content writer and communications officer for Shri Santosh Sikarwar (District Vice President, Bharatiya Janata Party / BJP, Agra, Uttar Pradesh).

The following short social media update was posted on his account:
"{raw_text}"
Date: {post_date or date.today().isoformat()}

Google Search Console requires comprehensive, high-quality, in-depth content (300+ words) to avoid "thin content" indexing issues.
Please expand this short update into a complete, professional, news-style article for his official website (santoshsikarwar.in).

Structure required:
1. Headline (Hindi, dignified, under 85 characters, no hashtags/emojis).
   CRITICAL SPELLING: The leader's name is "संतोष सिकरवार" (spelled "सिकरवार" with short 'ि', NEVER "सीकरवार").
2. Detailed Hindi Article (3-4 well-developed paragraphs, 250-350 words):
   - Ground report: What was the event/statement/meeting, who was present, where in Agra/Braj region it took place.
   - Core message: Organizational strengthening, public welfare, dedication to society, government policies if relevant.
   - Values: "सेवा ही संकल्प, संगठन ही शक्ति" and "राष्ट्र प्रथम, संगठन सर्वोपरि".
3. English Section (2 paragraphs at the end, separated by '———\\n\\nEnglish'):
   - Professional English translation/summary so Google indexes the article for both English and Hindi searches.

Return your response in valid JSON with these exact keys:
{{
  "title": "Hindi headline",
  "text": "Full article text in Hindi with the English section at the end",
  "category": "One of: कार्यक्रम, जनसंपर्क, संगठनात्मक गतिविधि, सामाजिक गतिविधि, बैठक, सम्मान, अन्य",
  "location": "e.g. आगरा, उत्तर प्रदेश"
}}
Return ONLY raw JSON, with no markdown code fences."""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-lite-latest:generateContent?key={api_key}"
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 4096,
            "responseMimeType": "application/json"
        }
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    import ssl
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            out_str = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            out_str = re.sub(r"^```json\s*", "", out_str)
            out_str = re.sub(r"\s*```$", "", out_str)
            parsed = json.loads(out_str)
            log("AI expanded article successfully into 300+ words with bilingual sections!")
            return parsed
    except Exception as e:
        log(f"Gemini expansion note ({e}), proceeding with original text.")
        return None


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


def launch_playwright_browser(p):
    """Launch Chrome on Windows or Chromium on Linux (for GitHub Actions / cross-platform)."""
    args = ["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-dev-shm-usage"]
    try:
        return p.chromium.launch(channel="chrome", headless=True, args=args)
    except Exception:
        return p.chromium.launch(headless=True, args=args)


def fetch_twitter_post(url_or_id):
    """Fetch post details from Twitter / X using syndication, playwright, or profile timeline."""
    raw = str(url_or_id).strip()

    # 1. Check if it's a specific tweet URL or tweet ID
    tweet_id_match = re.search(r"(?:status|statuses)/(\d+)", raw)
    if tweet_id_match:
        tweet_id = tweet_id_match.group(1)
    elif raw.isdigit():
        tweet_id = raw
    else:
        # Profile URL or screen name (e.g. https://x.com/BJP4UP or @BJP4UP)
        username_match = re.search(r"(?:x\.com|twitter\.com)/([a-zA-Z0-9_]+)", raw)
        screen_name = username_match.group(1) if username_match else raw.lstrip("@").strip()
        log(f"Profile URL detected for @{screen_name}. Fetching latest tweet...")

        tweet_id = None
        # Try syndication endpoint first
        timeline_url = f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{screen_name}"
        req = urllib.request.Request(
            timeline_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode("utf-8")
            m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html)
            if m:
                data = json.loads(m.group(1))
                entries = data["props"]["pageProps"]["timeline"]["entries"]
                tweets = [e["content"]["tweet"] for e in entries if "tweet" in e.get("content", {})]
                if tweets:
                    tweet_id = tweets[0]["id_str"]
                    log(f"Found tweet ID {tweet_id} via syndication API.")
        except Exception:
            pass

        # If syndication failed or gave 429, use Playwright Chrome to get tweet ID
        if not tweet_id:
            log(f"Fetching @{screen_name} timeline via browser...")
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = launch_playwright_browser(p)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = context.new_page()
                page.goto(f"https://x.com/{screen_name}", timeout=25000)
                page.wait_for_timeout(4000)

                links = page.locator("a[href*='/status/']").all()
                for l in links:
                    href = l.get_attribute("href") or ""
                    m = re.search(r"/status/(\d+)", href)
                    if m:
                        tweet_id = m.group(1)
                        log(f"Found tweet ID {tweet_id} from @{screen_name} timeline via browser!")
                        break
                browser.close()

        if not tweet_id:
            raise RuntimeError(f"Could not find any recent tweets for @{screen_name}")

    # 2. Fetch full tweet details via syndication endpoint
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
            if "T" in created_at_raw:
                post_date = created_at_raw.split("T")[0]
            else:
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

    user_screen_name = data.get("user", {}).get("screen_name") or "twitter"
    canonical_url = f"https://x.com/{user_screen_name}/status/{tweet_id}"
    return {
        "platform": "twitter",
        "url": canonical_url,
        "text": text,
        "date": post_date,
        "photos": photos,
    }


def fetch_facebook_post(url):
    """Fetch post details from Facebook using system Chrome via Playwright or fallback metadata."""
    log(f"Fetching Facebook content from: {url}")
    from playwright.sync_api import sync_playwright

    text = ""
    photos = []
    post_date = date.today().isoformat()

    with sync_playwright() as p:
        browser = launch_playwright_browser(p)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 1000}
        )
        page = context.new_page()

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(4000)
            page.evaluate("window.scrollBy(0, 1000)")
            page.wait_for_timeout(2000)

            # Click any "See more" buttons if present
            for btn in page.locator('text="See more"').all()[:5]:
                try:
                    btn.click(timeout=1000)
                except Exception:
                    pass

            articles = page.locator('div[role="article"]').all()
            log(f"Found {len(articles)} Facebook article containers.")

            chosen_article = None
            # Scan articles: skip pinned posts if another post exists, find one with good text and photos
            for a in articles:
                raw_a_text = a.inner_text().strip()
                # Skip comments
                if any(x in raw_a_text for x in ["Reply", "View more comments", "Write a comment"]):
                    pass
                # Check if it has author text
                if "Pinned post" in raw_a_text and len(articles) > 1:
                    if not chosen_article:
                        chosen_article = a
                    continue
                # If it's a post with text
                if len(raw_a_text) > 20:
                    chosen_article = a
                    break

            if chosen_article is None and articles:
                chosen_article = articles[0]

            if chosen_article:
                art_text = chosen_article.inner_text().strip()
                lines = [l.strip() for l in art_text.splitlines() if l.strip()]
                clean_lines = []
                collecting = False
                for line in lines:
                    if any(t in line for t in ["ago", "yesterday", "·", "August", "September", "October", "November", "December", "January", "February", "March", "April", "May", "June", "July"]):
                        collecting = True
                        continue
                    if any(stop_k in line for stop_k in ["All reactions:", "Like", "Comment", "Share", "View more"]):
                        break
                    if collecting and len(line) > 2:
                        clean_lines.append(line)

                if clean_lines:
                    text = " ".join(clean_lines)
                elif art_text:
                    filtered = [l for l in lines if not any(k in l for k in ["Santosh Sikarwar", "Like", "Comment", "Share", "All reactions:", "others", "Pinned post", "·"])]
                    if filtered:
                        text = " ".join(filtered)

                # Extract images from chosen article
                for img in chosen_article.locator("img").all():
                    src = img.get_attribute("src") or ""
                    if "scontent" in src and not any(k in src for k in ["rsrc.php", "emoji", "static"]):
                        if src not in photos:
                            photos.append(src)

            # Fallback if no article text extracted
            if not text:
                og_desc = page.locator('meta[property="og:description"]').get_attribute("content")
                if og_desc and not any(k in og_desc for k in ["Log in", "Facebook", "Sign up"]):
                    text = og_desc

            # Fallback photos if empty
            if not photos:
                og_img = page.locator('meta[property="og:image"]').get_attribute("content")
                if og_img and not og_img.endswith("rsrc.php"):
                    photos.append(og_img)

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
    """Format and save imported post into data/feed.json with AI expansion."""
    raw_text = item.get("text") or ""
    if not raw_text.strip():
        raise ValueError("Could not extract any text from this post.")

    # Load existing feed
    with open(FEED_PATH, "r", encoding="utf-8") as fh:
        feed = json.load(fh)

    existing_slugs = {p.get("slug") for p in feed.get("posts", []) if p.get("slug")}

    # Check for duplicate by URL or content
    post_url = item.get("url")
    clean_raw = re.sub(r"\s+", " ", raw_text).strip()
    for p in feed.get("posts", []):
        if post_url and p.get("source", {}).get("url") == post_url:
            log(f"Post already imported previously as slug: '{p.get('slug')}'")
            return None
        p_text = p.get("text") or ""
        p_excerpt = p.get("excerpt") or ""
        if len(clean_raw) > 20 and (clean_raw[:35] in p_text or clean_raw[:35] in p_excerpt):
            log(f"Post content already imported previously as slug: '{p.get('slug')}'")
            return None

    words = len(re.findall(r"\S+", raw_text))
    log(f"Original post word count: {words} words.")

    # AI Expansion for Google Search Console compliance
    ai_data = None
    if words < 180:
        log("Post is under 180 words. Using Gemini AI to expand into a full 300+ word article (to prevent Google thin content penalty)...")
        ai_data = expand_with_gemini(raw_text, item.get("date"))

    if ai_data and ai_data.get("text"):
        final_text = ai_data["text"]
        title = ai_data.get("title") or make_title(final_text)
        category = ai_data.get("category") or categorize(final_text)
        location = ai_data.get("location") or location
    else:
        final_text = raw_text
        title = make_title(final_text)
        category = categorize(final_text)

    # Enforce correct spelling of सिकरवार (short 'ि')
    final_text = final_text.replace("सीकरवार", "सिकरवार")
    title = title.replace("सीकरवार", "सिकरवार")

    if not title:
        title = f"संतोष सिकरवार - {item.get('date')}"

    base_slug = make_slug(title)
    if not base_slug:
        base_slug = "samachar"
    slug = base_slug
    counter = 2
    while slug in existing_slugs:
        slug = f"{base_slug}-{counter}"
        counter += 1

    excerpt = make_excerpt(final_text)

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
        "text": final_text,
        "gallery": gallery,
        "author": AUTHOR,
        "featured": False,
        "published": True,
        "updated_at": "",
        "source": {
            "platform": item.get("platform", "social"),
            "url": post_url,
            "imported_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
    }

    # Append new post and sort newer first (date descending)
    feed["posts"].append(new_post)
    feed["posts"].sort(key=lambda p: (p.get("date") or "", p.get("slug") or ""), reverse=True)

    with open(FEED_PATH, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(feed, fh, ensure_ascii=False, indent=2)

    final_words = len(re.findall(r"\S+", final_text))
    log(f"Successfully saved article: '{title}' ({final_words} words, slug: {slug})")
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
        # Pull any background remote commits (e.g. from GitHub Actions)
        subprocess.run(["git", "pull", "--no-rebase", "-X", "ours", "origin", "main"], cwd=ROOT, check=False)
        subprocess.run(["git", "push", "origin", "main"], cwd=ROOT, check=True)
        log("Published live to GitHub successfully!")
    except subprocess.CalledProcessError as e:
        log(f"Git push warning: {e}")


def process_url(url, push_live=True):
    """Import, format with AI, build static pages, and push live."""
    url = url.strip()
    if not url:
        return None

    log(f"Processing URL: {url}")
    if "twitter.com" in url or "x.com" in url:
        item = fetch_twitter_post(url)
    elif "facebook.com" in url or "fb.watch" in url:
        item = fetch_facebook_post(url)
    else:
        raise ValueError(f"Unrecognized social platform URL: {url}")

    post = add_post_to_feed(item)
    if not post:
        log("Post has already been imported previously. No changes needed.")
        return None

    # Re-build static pages & sitemaps
    log("Rebuilding static pages & sitemaps...")
    run_build_static_pages()

    if push_live:
        git_publish(post["title"])

    print("\n" + "=" * 60)
    print(f"DONE! Article is LIVE at:")
    print(f"  https://santoshsikarwar.in/samachar/{post['slug']}/")
    print("=" * 60 + "\n")
    return post


MONITORED_SOURCES = [
    {
        "name": "ठा. संतोष सिकरवार (Facebook)",
        "url": "https://www.facebook.com/Santoshsikarwarbjpagra/",
        "platform": "facebook",
    },
    {
        "name": "ठा. संतोष सिकरवार (Twitter / X)",
        "url": "https://x.com/ssikarwarbjp",
        "platform": "twitter",
    },
    {
        "name": "BJP Uttar Pradesh (Twitter / X)",
        "url": "https://x.com/BJP4UP",
        "platform": "twitter",
    },
]


def run_autopilot(loop=False, interval_minutes=120, push_live=True):
    """Scan all monitored social accounts for new posts, import new ones, and push live."""
    import time
    log("========================================================")
    log("  Santosh Sikarwar Website - Social Media Autopilot Sync")
    log("========================================================")

    while True:
        log(f"\n[Autopilot] Scanning {len(MONITORED_SOURCES)} sources at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}...")
        new_posts = []

        for src in MONITORED_SOURCES:
            name = src["name"]
            url = src["url"]
            platform = src["platform"]
            log(f"\n[Autopilot] Checking {name}...")
            try:
                if platform == "twitter":
                    item = fetch_twitter_post(url)
                else:
                    item = fetch_facebook_post(url)

                if not item or not item.get("text"):
                    log(f"[Autopilot] No text retrieved from {name}.")
                    continue

                post = add_post_to_feed(item)
                if post:
                    log(f"[Autopilot] SUCCESS: New post imported: '{post['title']}' (slug: {post['slug']})")
                    new_posts.append(post)
                else:
                    log(f"[Autopilot] {name} is up to date (no new post).")
            except Exception as e:
                log(f"[Autopilot] Note for {name}: {e}")

        if new_posts:
            log(f"\n[Autopilot] {len(new_posts)} new post(s) imported. Rebuilding static pages & sitemaps...")
            run_build_static_pages()
            if push_live:
                git_publish(f"Autopilot synced {len(new_posts)} new post(s)")
            log(f"[Autopilot] All {len(new_posts)} new post(s) are now LIVE on https://santoshsikarwar.in/!")
        else:
            log("\n[Autopilot] All accounts are already up to date. No new posts to publish.")

        if not loop:
            break

        next_time = datetime.now().timestamp() + (interval_minutes * 60)
        next_str = datetime.fromtimestamp(next_time).strftime('%H:%M:%S')
        log(f"\n[Autopilot] Sleeping for {interval_minutes} minutes. Next check at {next_str}...")
        log("[Autopilot] (Keep this running while you are out. Press Ctrl+C to stop.)")
        try:
            time.sleep(interval_minutes * 60)
        except KeyboardInterrupt:
            log("\n[Autopilot] Stopped by user.")
            break


def main():
    parser = argparse.ArgumentParser(description="Import social media posts to santoshsikarwar.in")
    parser.add_argument("--url", help="Twitter (X) or Facebook post URL")
    parser.add_argument("--autopilot", action="store_true", help="Automatically check all monitored accounts for new posts")
    parser.add_argument("--loop", action="store_true", help="Run continuously in background loop (autopilot mode)")
    parser.add_argument("--interval", type=int, default=120, help="Check interval in minutes (default: 120)")
    parser.add_argument("--no-push", action="store_true", help="Do not git push after building")
    args = parser.parse_args()

    if args.autopilot or args.loop:
        run_autopilot(loop=args.loop, interval_minutes=args.interval, push_live=not args.no_push)
        return

    url = args.url
    if not url:
        print("========================================================")
        print("  Santosh Sikarwar Website - Social Media Importer (AI-Powered)")
        print("========================================================")
        print("Modes:")
        print("  1. Paste a specific post URL to import immediately.")
        print("  2. Leave blank and press Enter to run Autopilot on all accounts.")
        url = input("\nPaste post URL (or press Enter for Autopilot): ").strip()

    if url:
        process_url(url, push_live=not args.no_push)
    else:
        run_autopilot(loop=False, push_live=not args.no_push)


if __name__ == "__main__":
    main()
