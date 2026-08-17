#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
import_facebook.py
====================================================================
Import genuine posts from the Santosh Sikarwar **Facebook Page** into
data/feed.json using the OFFICIAL Meta Graph API. No scraping, no browser
automation, no undocumented endpoints.

Pipeline:
    Facebook Page post  ->  Graph API  ->  this importer  ->  feed.json
    ->  generate_sitemaps.py  ->  sitemaps  ->  GitHub Pages

Secrets come ONLY from environment variables (GitHub Actions Secrets):
    META_PAGE_ID              (required)
    META_PAGE_ACCESS_TOKEN    (required)  long-lived Page access token
    META_APP_SECRET           (optional)  enables appsecret_proof (recommended)
    GRAPH_VERSION             (optional)  e.g. "v21.0" (default below)

Never commit these. Never print the token.

Usage:
    python import_facebook.py --dry-run     # show what WOULD be imported, no writes
    python import_facebook.py               # perform the import

The importer is idempotent: it stores each Facebook post_id in feed.json and
skips posts already imported, so running it twice makes no changes.
"""

import argparse
import datetime
import hashlib
import hmac
import json
import os
import re
import sys
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
FEED_PATH = os.path.join(ROOT, "data", "feed.json")
IMAGES_DIR = os.path.join(ROOT, "images")
GRAPH_VERSION = os.environ.get("GRAPH_VERSION", "v21.0")
GRAPH = "https://graph.facebook.com/" + GRAPH_VERSION
AUTHOR = "संतोष सिकरवार"
VALID_CATEGORIES = ["कार्यक्रम", "जनसंपर्क", "संगठनात्मक गतिविधि", "सामाजिक गतिविधि", "बैठक", "सम्मान", "अन्य"]


def warn(msg):
    print("  ! " + msg, file=sys.stderr)


# ---------- text cleaning ----------
_URL_RE = re.compile(r"https?://\S+")
_HASHTAG_RE = re.compile(r"[#＃]\S+")
_EMOJI_RE = re.compile(
    "[" 
    "\U0001F300-\U0001FAFF"
    "\U00002600-\U000027BF"
    "\U0001F1E6-\U0001F1FF"
    "\U00002190-\U000021FF"
    "\U00002B00-\U00002BFF"
    "\U0000FE0F\U0000200D"
    "]", flags=re.UNICODE)


def _strip_noise(text):
    text = _URL_RE.sub("", text)
    text = _HASHTAG_RE.sub("", text)
    text = _EMOJI_RE.sub("", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def make_title(message):
    """Deterministic title: first heading/sentence, cleaned, length-limited."""
    if not message:
        return ""
    # first non-empty line
    line = ""
    for ln in message.splitlines():
        if _strip_noise(ln):
            line = _strip_noise(ln)
            break
    if not line:
        return ""
    # if the line is long, take its first sentence
    words = line.split()
    if len(words) > 14:
        m = re.split(r"[।!?\.]", line)
        line = (m[0] if m and m[0].strip() else line).strip()
    # length limit (~80 chars, cut on a word boundary)
    if len(line) > 80:
        cut = line[:80]
        sp = cut.rfind(" ")
        line = (cut[:sp] if sp > 40 else cut).strip()
    return line.strip(" -–—:।")


def clean_body(message):
    """Keep the original post text; only clean technical noise."""
    if not message:
        return ""
    text = _URL_RE.sub("", message)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def make_excerpt(message, limit=140):
    cleaned = _strip_noise((message or "").replace("\n", " "))
    if not cleaned:
        return ""
    m = re.split(r"[।!?\.]", cleaned)
    first = (m[0].strip() if m and m[0].strip() else cleaned)
    if len(first) <= limit:
        return first
    cut = first[:limit]
    sp = cut.rfind(" ")
    return (cut[:sp] if sp > 60 else cut).strip() + "…"


# ---------- category ----------
_CATEGORY_RULES = [
    ("बैठक", "बैठक"),
    ("मुलाकात", "जनसंपर्क"),
    ("जनसंपर्क", "जनसंपर्क"),
    ("जनसुनवाई", "जनसंपर्क"),
    ("कार्यक्रम", "कार्यक्रम"),
    ("आयोजन", "कार्यक्रम"),
    ("उद्घाटन", "कार्यक्रम"),
    ("शिलान्यास", "कार्यक्रम"),
    ("श्रद्धांजलि", "सम्मान"),
    ("पुण्यतिथि", "सम्मान"),
    ("जयंती", "सम्मान"),
    ("सम्मान", "सम्मान"),
    ("सदस्यता", "संगठनात्मक गतिविधि"),
    ("संगठन", "संगठनात्मक गतिविधि"),
    ("कार्यसमिति", "संगठनात्मक गतिविधि"),
    ("वृक्षारोपण", "सामाजिक गतिविधि"),
    ("स्वच्छता", "सामाजिक गतिविधि"),
    ("रक्तदान", "सामाजिक गतिविधि"),
    ("सेवा", "सामाजिक गतिविधि"),
]


def categorize(text):
    for kw, cat in _CATEGORY_RULES:
        if kw in (text or ""):
            return cat
    return "अन्य"


# ---------- Hindi -> Roman slug ----------
PROPER_NOUNS = {
    "आगरा": "agra", "भाजपा": "bjp", "बीजेपी": "bjp", "भारतीय": "bharatiya",
    "जनता": "janata", "पार्टी": "party", "संतोष": "santosh", "सिकरवार": "sikarwar",
    "फतेहपुर": "fatehpur", "सीकरी": "sikri", "ब्रज": "braj", "किसान": "kisan",
    "मोर्चा": "morcha", "बैठक": "baithak", "कार्यकर्ता": "karyakarta",
    "कार्यकर्ताओं": "karyakartaon", "उत्तर": "uttar", "प्रदेश": "pradesh",
    "जिला": "jila", "उपाध्यक्ष": "upadhyaksh", "कार्यक्रम": "karyakram",
    "जनसंपर्क": "jansampark", "संगठन": "sangathan", "मुख्यमंत्री": "mukhyamantri",
    "प्रधानमंत्री": "pradhanmantri", "योगी": "yogi", "आदित्यनाथ": "adityanath",
}
_DEVA_VOWELS = {"अ": "a", "आ": "a", "इ": "i", "ई": "i", "उ": "u", "ऊ": "u", "ऋ": "ri",
                "ए": "e", "ऐ": "ai", "ओ": "o", "औ": "au", "ऍ": "e", "ऑ": "o"}
_DEVA_MATRA = {"ा": "a", "ि": "i", "ी": "i", "ु": "u", "ू": "u", "ृ": "ri",
               "े": "e", "ै": "ai", "ो": "o", "ौ": "au", "ॉ": "o", "ॅ": "e"}
_DEVA_CONS = {
    "क": "k", "ख": "kh", "ग": "g", "घ": "gh", "ङ": "n",
    "च": "ch", "छ": "chh", "ज": "j", "झ": "jh", "ञ": "n",
    "ट": "t", "ठ": "th", "ड": "d", "ढ": "dh", "ण": "n",
    "त": "t", "थ": "th", "द": "d", "ध": "dh", "न": "n",
    "प": "p", "फ": "ph", "ब": "b", "भ": "bh", "म": "m",
    "य": "y", "र": "r", "ल": "l", "व": "v", "श": "sh", "ष": "sh",
    "स": "s", "ह": "h", "ळ": "l",
}


def _translit_word(w):
    w = w.replace("\u093c", "")  # drop nukta for slug simplicity
    chars = list(w)
    out = []
    i, n = 0, len(chars)
    while i < n:
        c = chars[i]
        if c in _DEVA_CONS:
            out.append(_DEVA_CONS[c])
            nxt = chars[i + 1] if i + 1 < n else ""
            if nxt == "\u094d":            # virama -> no vowel
                i += 2
                continue
            if nxt in _DEVA_MATRA:
                out.append(_DEVA_MATRA[nxt])
                i += 2
                continue
            out.append("a")                # inherent vowel
            i += 1
            continue
        if c in _DEVA_VOWELS:
            out.append(_DEVA_VOWELS[c]); i += 1; continue
        if c in ("ं", "ँ"):
            out.append("n"); i += 1; continue
        if c == "ः":
            out.append("h"); i += 1; continue
        if c in ("ऽ", "\u094d"):
            i += 1; continue
        out.append(c); i += 1          # keep latin/digits as-is
    return "".join(out)


def make_slug(title, fallback=""):
    words = re.split(r"\s+", (title or "").strip())
    parts = []
    for w in words:
        key = re.sub(r"[^\u0900-\u097Fa-zA-Z0-9]", "", w)
        if not key:
            continue
        if key in PROPER_NOUNS:
            parts.append(PROPER_NOUNS[key])
        elif re.match(r"^[A-Za-z0-9]+$", key):
            parts.append(key.lower())
        else:
            parts.append(_translit_word(key))
    slug = "-".join(parts).lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    if len(slug) > 60:
        slug = slug[:60].rsplit("-", 1)[0].strip("-")
    return slug or fallback


def make_date(created_time):
    """Facebook created_time (ISO 8601) -> YYYY-MM-DD (original publication date)."""
    if not created_time:
        return ""
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", created_time)
    return m.group(0) if m else ""


# ---------- Meta Graph API ----------
def graph_get(path, params):
    token = os.environ["META_PAGE_ACCESS_TOKEN"]
    q = dict(params)
    q["access_token"] = token
    secret = os.environ.get("META_APP_SECRET")
    if secret:
        q["appsecret_proof"] = hmac.new(secret.encode("utf-8"), token.encode("utf-8"),
                                        hashlib.sha256).hexdigest()
    url = GRAPH + "/" + path + "?" + urllib.parse.urlencode(q)
    req = urllib.request.Request(url, headers={"User-Agent": "santoshsikarwar-importer"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode("utf-8"))
    if isinstance(data, dict) and data.get("error"):
        raise RuntimeError("Graph API error: " + json.dumps(data["error"], ensure_ascii=False))
    return data


def fetch_posts(page_id, limit):
    fields = ("id,message,created_time,permalink_url,place,"
              "attachments{media_type,type,media,subattachments{data{media,type}}}")
    data = graph_get(page_id + "/published_posts", {"fields": fields, "limit": str(limit)})
    return data.get("data", [])


def extract_images(post):
    srcs = []
    for a in (post.get("attachments", {}).get("data", []) or []):
        img = (a.get("media", {}) or {}).get("image", {}) or {}
        if img.get("src"):
            srcs.append(img["src"])
        for s in ((a.get("subattachments", {}) or {}).get("data", []) or []):
            si = (s.get("media", {}) or {}).get("image", {}) or {}
            if si.get("src"):
                srcs.append(si["src"])
    seen, out = set(), []
    for s in srcs:
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


def download_image(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": "santoshsikarwar-importer"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    if not data:
        raise RuntimeError("empty image")
    with open(dest, "wb") as f:
        f.write(data)


def image_filename(date, slug, count):
    base = "facebook-%s-%s" % (date, (slug[:32].strip("-") or "post"))
    name = base + (".jpg" if count == 0 else "-%d.jpg" % (count + 1))
    path = os.path.join(IMAGES_DIR, name)
    n = 2
    while os.path.exists(path):
        name = base + "-%d.jpg" % n
        path = os.path.join(IMAGES_DIR, name)
        n += 1
    return name, path


# ---------- main ----------
def main():
    ap = argparse.ArgumentParser(description="Import Facebook Page posts into feed.json")
    ap.add_argument("--dry-run", action="store_true", help="show what would be imported; write nothing")
    ap.add_argument("--limit", type=int, default=25, help="recent posts to fetch (default 25)")
    args = ap.parse_args()

    page_id = os.environ.get("META_PAGE_ID")
    if not page_id or not os.environ.get("META_PAGE_ACCESS_TOKEN"):
        print("ERROR: META_PAGE_ID and META_PAGE_ACCESS_TOKEN environment variables are required.")
        sys.exit(2)

    with open(FEED_PATH, "r", encoding="utf-8") as f:
        feed = json.load(f)
    posts_list = feed.get("posts", [])
    existing_ids = {(p.get("source") or {}).get("post_id") for p in posts_list if p.get("source")}
    existing_slugs = {p.get("slug") for p in posts_list if p.get("slug")}

    try:
        fb_posts = fetch_posts(page_id, args.limit)
    except Exception as exc:
        print("ERROR: Meta Graph API request failed: %s" % exc)
        sys.exit(1)

    new_entries = []
    for post in fb_posts:
        pid = post.get("id")
        if not pid:
            warn("post without id skipped")
            continue
        if pid in existing_ids:
            continue  # already imported -> idempotent skip
        message = post.get("message") or ""
        images = extract_images(post)
        if not message.strip() and not images:
            warn("post %s has no text or media, skipped" % pid)
            continue

        date = make_date(post.get("created_time"))
        if not date:
            warn("post %s has invalid/missing date, skipped" % pid)
            continue

        pid_tail = re.sub(r"\W", "", pid)[-12:]
        title = make_title(message) or ("गतिविधि " + pid_tail)
        slug = make_slug(title, fallback="facebook-" + pid_tail)
        base, n = slug, 2
        taken = existing_slugs.union({e["slug"] for e in new_entries})
        while slug in taken:
            slug = "%s-%d" % (base, n)
            n += 1

        entry = {
            "title": title,
            "slug": slug,
            "date": date,
            "location": (post.get("place") or {}).get("name", "") or "",
            "category": categorize(message),
            "image": "",
            "image_alt": "",
            "excerpt": make_excerpt(message),
            "text": clean_body(message),
            "gallery": [],
            "author": AUTHOR,
            "featured": False,
            "published": True,
            "updated_at": "",
            "source": {
                "platform": "facebook",
                "post_id": pid,
                "url": post.get("permalink_url", ""),
                "imported_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
        }

        if not args.dry_run:
            saved = []
            for src in images:
                fn, dest = image_filename(date, slug, len(saved))
                try:
                    download_image(src, dest)
                    saved.append("/images/" + fn)
                except Exception as exc:
                    warn("image download failed for %s: %s" % (pid, exc))
            if saved:
                entry["image"] = saved[0]
                entry["image_alt"] = title  # conservative: title as alt
                entry["gallery"] = [{"src": s, "caption": ""} for s in saved[1:]]

        print("NEW  %s" % pid)
        print("     title    : %s" % title)
        print("     slug     : %s" % slug)
        print("     date     : %s" % date)
        print("     category : %s" % entry["category"])
        print("     location : %s" % (entry["location"] or "(none)"))
        print("     images   : %d" % len(images))
        new_entries.append(entry)

    if not new_entries:
        print("No new Facebook posts to import.")
        return
    if args.dry_run:
        print("\nDRY-RUN: %d new post(s) would be imported. feed.json NOT modified." % len(new_entries))
        return

    new_entries.sort(key=lambda e: e["date"], reverse=True)
    feed["posts"] = new_entries + posts_list
    with open(FEED_PATH, "w", encoding="utf-8", newline="\n") as f:
        json.dump(feed, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("\nImported %d new post(s) into feed.json. Now run: python generate_sitemaps.py" % len(new_entries))


if __name__ == "__main__":
    main()
