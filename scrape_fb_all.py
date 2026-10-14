import sys
import json
import re
from datetime import datetime, date
from playwright.sync_api import sync_playwright

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

posts = []

with sync_playwright() as p:
    args = ["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-dev-shm-usage"]
    try:
        browser = p.chromium.launch(channel="chrome", headless=True, args=args)
    except Exception:
        browser = p.chromium.launch(headless=True, args=args)
    
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 1000}
    )
    page = context.new_page()
    page.goto("https://www.facebook.com/Santoshsikarwarbjpagra/", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(4000)

    # Click "See more" buttons if present
    for btn in page.locator('text="See more"').all()[:20]:
        try:
            btn.click(timeout=800)
        except Exception:
            pass

    for _ in range(4):
        page.evaluate("window.scrollBy(0, 1500)")
        page.wait_for_timeout(1500)

    for btn in page.locator('text="See more"').all()[:20]:
        try:
            btn.click(timeout=800)
        except Exception:
            pass

    articles = page.locator('div[role="article"]').all()
    print(f"Extracted {len(articles)} articles.")

    for idx, a in enumerate(articles):
        raw_text = a.inner_text().strip()
        lines = [l.strip() for l in raw_text.splitlines() if l.strip()]

        # Filter out UI noise
        content_lines = []
        date_line = ""
        collecting = False
        for l in lines:
            if not date_line and any(m in l for m in ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December", "yesterday", "hrs", "ago", "·"]):
                date_line = l
                collecting = True
                continue
            if any(stop_k in l for stop_k in ["All reactions:", "Like", "Comment", "Share", "View more", "Write a comment"]):
                break
            if collecting and len(l) > 2 and not any(ign in l for ign in ["Santosh Sikarwar", "Pinned post", "Public"]):
                content_lines.append(l)

        # Get photos
        photos = []
        for img in a.locator("img").all():
            src = img.get_attribute("src") or ""
            if "scontent" in src and not any(k in src for k in ["rsrc.php", "emoji", "static"]):
                if src not in photos:
                    photos.append(src)

        clean_text = " ".join(content_lines).strip()
        if not clean_text and len(lines) > 2:
            # Fallback
            clean_text = " ".join([l for l in lines if not any(k in l for k in ["Santosh Sikarwar", "Like", "Comment", "Share", "All reactions:", "others", "Pinned post", "·"])][:4])

        if clean_text:
            posts.append({
                "index": idx + 1,
                "date_hint": date_line,
                "text": clean_text,
                "photos_count": len(photos),
                "photos": photos[:3]
            })

    browser.close()

with open("scratch_fb_posts.json", "w", encoding="utf-8") as f:
    json.dump(posts, f, ensure_ascii=False, indent=2)

print(f"Saved {len(posts)} posts to scratch_fb_posts.json")
for p in posts[:8]:
    print(f"[{p['index']}] Date: {p['date_hint']} | Photos: {p['photos_count']} | Text: {p['text'][:80]}...")
