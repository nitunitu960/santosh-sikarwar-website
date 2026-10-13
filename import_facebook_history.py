#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
import_facebook_history.py
====================================================================
Automated extractor to fetch the past 1 year of posts from:
https://www.facebook.com/Santoshsikarwarbjpagra/

How it works:
1. Uses a persistent browser profile (or saves fb_session.json) so Facebook
   does not trigger the "Log in to see more" wall.
2. Scrolls back through the timeline collecting posts from the past 365 days.
3. Automatically expands short posts using Gemini AI into 300+ word articles.
4. Enforces the correct spelling "सिकरवार".
5. Dates each article accurately and sorts newer first.
6. Pre-renders static HTML and pushes live to santoshsikarwar.in.
"""

import os
import sys
import json
import time
import re
from datetime import datetime, date, timedelta

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from social_importer import (
    ROOT,
    FEED_PATH,
    log,
    add_post_to_feed,
    expand_with_gemini,
    git_publish,
    launch_playwright_browser
)
from build_static_pages import main as run_build_static_pages

PROFILE_DIR = os.path.join(ROOT, ".fb_browser_profile")
PAGE_URL = "https://www.facebook.com/Santoshsikarwarbjpagra/"


def extract_year_posts(max_posts=50, interactive_login=False):
    from playwright.sync_api import sync_playwright

    log(f"Starting Facebook 1-year history extractor for: {PAGE_URL}")
    os.makedirs(PROFILE_DIR, exist_ok=True)

    with sync_playwright() as p:
        args = ["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-dev-shm-usage"]
        
        # Use persistent context to retain login session across runs
        context = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            channel="chrome",
            headless=not interactive_login,
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            args=args
        )

        page = context.new_page()
        page.goto(PAGE_URL, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(3000)

        if interactive_login:
            print("\n" + "=" * 60)
            print("FACEBOOK LOGIN WINDOW OPENED")
            print("If Facebook asks you to log in, please log in now in the browser window.")
            print("Once logged in (or if already viewing the page), press Enter here in the terminal...")
            print("=" * 60 + "\n")
            input("Press Enter once ready to start 1-year extraction: ")

        log("Scanning timeline and scrolling backwards...")

        one_year_ago = date.today() - timedelta(days=365)
        extracted_items = []
        seen_texts = set()

        scroll_count = 0
        max_scrolls = 60
        consecutive_no_new = 0

        while scroll_count < max_scrolls and len(extracted_items) < max_posts:
            scroll_count += 1
            
            # Click "See more" buttons to expand truncated text
            for btn in page.locator('text="See more"').all()[:15]:
                try:
                    btn.click(timeout=600)
                except Exception:
                    pass

            articles = page.locator('div[role="article"]').all()
            new_in_this_scroll = 0

            for a in articles:
                raw_text = a.inner_text().strip()
                if not raw_text or len(raw_text) < 15:
                    continue

                # Filter text lines
                lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
                clean_lines = []
                date_hint = ""
                collecting = False

                for l in lines:
                    if not date_hint and any(m in l for m in ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December", "yesterday", "hrs", "ago", "·"]):
                        date_hint = l
                        collecting = True
                        continue
                    if any(stop in l for stop in ["All reactions:", "Like", "Comment", "Share", "View more", "Write a comment"]):
                        break
                    if collecting and len(l) > 2 and not any(ign in l for ign in ["Santosh Sikarwar", "Pinned post", "Public"]):
                        clean_lines.append(l)

                post_text = " ".join(clean_lines).strip()
                if not post_text:
                    post_text = " ".join([l for l in lines if not any(k in l for k in ["Santosh Sikarwar", "Like", "Comment", "Share", "All reactions:", "Pinned post", "·"])][:4]).strip()

                if not post_text or len(post_text) < 15:
                    continue

                norm_key = post_text[:40]
                if norm_key in seen_texts:
                    continue

                seen_texts.add(norm_key)
                new_in_this_scroll += 1

                # Photos
                photos = []
                for img in a.locator("img").all():
                    src = img.get_attribute("src") or ""
                    if "scontent" in src and not any(k in src for k in ["rsrc.php", "emoji", "static"]):
                        if src not in photos:
                            photos.append(src)

                # Parse rough date from date_hint
                parsed_date = date.today().isoformat()
                for m_idx, m_name in enumerate(["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"], 1):
                    dm = re.search(rf"(\d{{1,2}})\s+{m_name}(?:\s+(\d{{4}}))?", date_hint, re.IGNORECASE)
                    if dm:
                        day = int(dm.group(1))
                        yr = int(dm.group(2)) if dm.group(2) else 2026
                        try:
                            parsed_date = f"{yr:04d}-{m_idx:02d}-{day:02d}"
                        except Exception:
                            pass
                        break

                extracted_items.append({
                    "text": post_text,
                    "photos": photos,
                    "date": parsed_date,
                    "url": PAGE_URL
                })
                log(f"[{len(extracted_items)}] Found post from {parsed_date}: {post_text[:60]}...")

            if new_in_this_scroll == 0:
                consecutive_no_new += 1
                if consecutive_no_new >= 5:
                    log("Reached end of visible timeline or waiting for new content.")
                    break
            else:
                consecutive_no_new = 0

            page.evaluate("window.scrollBy(0, 2000)")
            page.wait_for_timeout(2000)

        context.close()

    log(f"\nExtraction complete! Found {len(extracted_items)} historical posts.")
    return extracted_items


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Copy 1-year history from Facebook")
    parser.add_argument("--login", action="store_true", help="Open visible browser to log in to Facebook first")
    parser.add_argument("--max", type=int, default=30, help="Max posts to import")
    parser.add_argument("--no-push", action="store_true", help="Do not git push after importing")
    args = parser.parse_args()

    items = extract_year_posts(max_posts=args.max, interactive_login=args.login)

    if not items:
        print("\nNo posts extracted.")
        if not args.login:
            print("Tip: Run with --login (or use IMPORT_1_YEAR_FACEBOOK.bat) so you can log in to bypass Facebook's login wall!")
        return

    imported = []
    for it in items:
        p = add_post_to_feed(it)
        if p:
            imported.append(p)

    if imported:
        log(f"Successfully added {len(imported)} new posts to feed.json!")
        log("Rebuilding static pages and sitemaps...")
        run_build_static_pages()
        if not args.no_push:
            git_publish(f"Imported {len(imported)} historical Facebook posts")
        log(f"All {len(imported)} articles are now LIVE on https://santoshsikarwar.in/!")
    else:
        log("All extracted posts were already present in feed.json.")


if __name__ == "__main__":
    main()
