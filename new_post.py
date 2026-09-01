#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
new_post.py
====================================================================
Turn a plain-text post (typed, or pasted from X / Facebook / WhatsApp)
into a complete, well-formed article in data/feed.json.

No API. No credentials. No cost. Works entirely offline.

It generates for you, deterministically:
    * title      - cleaned first line (hashtags / URLs / emojis stripped)
    * slug       - Hindi -> Roman transliteration, lowercase-hyphen, unique
    * excerpt    - first sentence, length-limited
    * category   - matched to an existing category by keyword
    * image_alt  - descriptive alt text (falls back to the title)
    * date       - the ORIGINAL date you give it (never today's date unless asked)

New articles are saved as DRAFTS (published: false) unless you pass --publish,
so nothing goes live until you are happy with it. Edit and publish from /admin.

--------------------------------------------------------------------
USAGE
--------------------------------------------------------------------
1. Put the post text in a file, e.g. draft.txt (first line becomes the title):

       खेरागढ़ में तिरंगा यात्रा
       (blank line)
       पूरा विवरण यहाँ...

2. Put any photos in the images/ folder, then run:

       python new_post.py --text draft.txt --date 2026-09-01 ^
              --image images/my-photo.jpg --location "आगरा, उत्तर प्रदेश"

3. Review, then publish from /admin (or re-run with --publish), and finally:

       python generate_sitemaps.py

Options:
    --text FILE        file containing the post text (required)
    --date YYYY-MM-DD  original date of the activity (required)
    --image PATH       featured photo already inside images/
    --gallery A,B,C    extra photos, comma-separated
    --location TEXT    e.g. "कागारौल, खेरागढ़, आगरा"
    --category TEXT    one of the existing categories (auto-detected if omitted)
    --title TEXT       override the auto-generated title
    --slug TEXT        override the auto-generated slug
    --alt TEXT         alt text for the featured photo
    --publish          publish immediately instead of saving as a draft
    --featured         mark as the featured article
    --dry-run          show what would be created; write nothing
"""

import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
FEED_PATH = os.path.join(ROOT, "data", "feed.json")
AUTHOR = "संतोष सिकरवार"
VALID_CATEGORIES = ["कार्यक्रम", "जनसंपर्क", "संगठनात्मक गतिविधि",
                    "सामाजिक गतिविधि", "बैठक", "सम्मान", "अन्य"]
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

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
    return re.sub(r"[ \t]+", " ", text).strip()


# Sentence boundary: danda, ! or ? — and a full stop only when it is NOT a
# decimal point (so "7.8 प्रतिशत" and "FY 2026-27" stay intact).
_SENT_RE = re.compile(r"।|[!?]|(?<!\d)\.(?!\d)")


def _first_sentence(text, fallback):
    parts = _SENT_RE.split(text)
    return parts[0].strip() if parts and parts[0].strip() else fallback


def make_title(body):
    for line in body.splitlines():
        cleaned = _strip_noise(line)
        if cleaned:
            break
    else:
        return ""
    if len(cleaned.split()) > 14:
        cleaned = _first_sentence(cleaned, cleaned)
    if len(cleaned) > 90:
        cut = cleaned[:90]
        sp = cut.rfind(" ")
        cleaned = (cut[:sp] if sp > 45 else cut).strip()
    return cleaned.strip(" -–—:।")


def make_excerpt(body, limit=150):
    cleaned = _strip_noise((body or "").replace("\n", " "))
    if not cleaned:
        return ""
    first = _first_sentence(cleaned, cleaned)
    if len(first) <= limit:
        return first + ("।" if not first.endswith("।") else "")
    cut = first[:limit]
    sp = cut.rfind(" ")
    return (cut[:sp] if sp > 70 else cut).strip() + "…"


# ---------- category ----------
_CATEGORY_RULES = [
    ("बैठक", "बैठक"), ("मुलाकात", "जनसंपर्क"), ("जनसंपर्क", "जनसंपर्क"),
    ("जनसुनवाई", "जनसंपर्क"), ("कार्यक्रम", "कार्यक्रम"), ("यात्रा", "कार्यक्रम"),
    ("आयोजन", "कार्यक्रम"), ("उद्घाटन", "कार्यक्रम"), ("शिलान्यास", "कार्यक्रम"),
    ("श्रद्धांजलि", "सम्मान"), ("पुण्यतिथि", "सम्मान"), ("जयंती", "सम्मान"),
    ("सम्मान", "सम्मान"), ("सदस्यता", "संगठनात्मक गतिविधि"),
    ("संगठन", "संगठनात्मक गतिविधि"), ("कार्यसमिति", "संगठनात्मक गतिविधि"),
    ("बूथ", "संगठनात्मक गतिविधि"), ("वृक्षारोपण", "सामाजिक गतिविधि"),
    ("स्वच्छता", "सामाजिक गतिविधि"), ("रक्तदान", "सामाजिक गतिविधि"),
    ("सेवा", "सामाजिक गतिविधि"),
]


def categorize(text):
    for keyword, category in _CATEGORY_RULES:
        if keyword in (text or ""):
            return category
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
    "खेरागढ़": "kheragarh", "खेरागढ": "kheragarh", "कागारौल": "kagarol",
    "तिरंगा": "tiranga", "यात्रा": "yatra", "बूथ": "booth", "विधानसभा": "vidhansabha",
    "श्रद्धांजलि": "shraddhanjali", "शुभकामनाएं": "shubhkamnaye",
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


def _translit_word(word):
    word = word.replace("\u093c", "")
    chars = list(word)
    out = []
    i, n = 0, len(chars)
    while i < n:
        c = chars[i]
        if c in _DEVA_CONS:
            out.append(_DEVA_CONS[c])
            nxt = chars[i + 1] if i + 1 < n else ""
            if nxt == "\u094d":
                i += 2
                continue
            if nxt in _DEVA_MATRA:
                out.append(_DEVA_MATRA[nxt])
                i += 2
                continue
            out.append("a")
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
        out.append(c); i += 1
    return "".join(out)


def make_slug(title):
    parts = []
    for word in re.split(r"\s+", (title or "").strip()):
        key = re.sub(r"[^\u0900-\u097Fa-zA-Z0-9]", "", word)
        if not key:
            continue
        if key in PROPER_NOUNS:
            parts.append(PROPER_NOUNS[key])
        elif re.match(r"^[A-Za-z0-9]+$", key):
            parts.append(key.lower())
        else:
            parts.append(_translit_word(key))
    slug = re.sub(r"[^a-z0-9]+", "-", "-".join(parts).lower())
    slug = re.sub(r"-+", "-", slug).strip("-")
    if len(slug) > 60:
        slug = slug[:60].rsplit("-", 1)[0].strip("-")
    return slug


def norm_image(value):
    if not value:
        return ""
    rel = value.strip().replace("\\", "/").lstrip("/")
    if not rel:
        return ""
    if not rel.startswith("images/"):
        rel = "images/" + rel
    return "/" + rel


def check_image(path_with_slash):
    rel = path_with_slash.lstrip("/")
    return os.path.isfile(os.path.join(ROOT, rel.replace("/", os.sep)))


def main():
    ap = argparse.ArgumentParser(description="Create a well-formed article in data/feed.json")
    ap.add_argument("--text", required=True, help="file containing the post text")
    ap.add_argument("--date", required=True, help="original date of the activity (YYYY-MM-DD)")
    ap.add_argument("--image", default="", help="featured photo inside images/")
    ap.add_argument("--gallery", default="", help="extra photos, comma-separated")
    ap.add_argument("--location", default="", help='e.g. "कागारौल, खेरागढ़, आगरा"')
    ap.add_argument("--category", default="", help="one of the existing categories")
    ap.add_argument("--title", default="", help="override the auto-generated title")
    ap.add_argument("--slug", default="", help="override the auto-generated slug")
    ap.add_argument("--alt", default="", help="alt text for the featured photo")
    ap.add_argument("--publish", action="store_true", help="publish now instead of saving a draft")
    ap.add_argument("--featured", action="store_true", help="mark as the featured article")
    ap.add_argument("--dry-run", action="store_true", help="show the result; write nothing")
    args = ap.parse_args()

    if not DATE_RE.match(args.date):
        print("ERROR: --date must be YYYY-MM-DD (the real date of the activity)")
        sys.exit(2)
    if not os.path.isfile(args.text):
        print("ERROR: text file not found: %s" % args.text)
        sys.exit(2)

    with open(args.text, encoding="utf-8") as fh:
        body = fh.read().strip()
    if not body:
        print("ERROR: %s is empty" % args.text)
        sys.exit(2)

    with open(FEED_PATH, encoding="utf-8") as fh:
        feed = json.load(fh)
    posts = feed.get("posts", [])
    taken = {p.get("slug") for p in posts if p.get("slug")}

    title = args.title.strip() or make_title(body)
    if not title:
        print("ERROR: could not derive a title; pass --title")
        sys.exit(2)

    slug = args.slug.strip() or make_slug(title)
    if not SLUG_RE.match(slug):
        print("ERROR: slug '%s' is invalid (use lowercase letters, digits, hyphens)" % slug)
        sys.exit(2)
    base, n = slug, 2
    while slug in taken:
        slug = "%s-%d" % (base, n)
        n += 1

    category = args.category.strip() or categorize(body)
    if category not in VALID_CATEGORIES:
        print("ERROR: category must be one of: %s" % ", ".join(VALID_CATEGORIES))
        sys.exit(2)

    featured_img = norm_image(args.image)
    gallery = []
    for item in [g for g in args.gallery.split(",") if g.strip()]:
        gallery.append(norm_image(item))

    warnings = []
    for img in ([featured_img] if featured_img else []) + gallery:
        if not check_image(img):
            warnings.append("photo not found in repo: %s" % img)

    word_count = len([w for w in body.split() if w.strip()])
    if word_count < 300:
        warnings.append(
            "body is only %d words. Google often declines to index short pages — "
            "aim for 300+ words of real detail (what happened, where, who took part)."
            % word_count)

    entry = {
        "title": title,
        "slug": slug,
        "date": args.date,
        "location": args.location.strip(),
        "category": category,
        "image": featured_img,
        "image_alt": (args.alt.strip() or title) if featured_img else "",
        "excerpt": make_excerpt(body),
        "text": body,
        "gallery": [{"src": g, "caption": ""} for g in gallery],
        "author": AUTHOR,
        "featured": bool(args.featured),
        "published": bool(args.publish),
        "updated_at": "",
    }

    print("title     : %s" % entry["title"])
    print("slug      : %s" % entry["slug"])
    print("date      : %s" % entry["date"])
    print("category  : %s" % entry["category"])
    print("location  : %s" % (entry["location"] or "(none)"))
    print("image     : %s" % (entry["image"] or "(none)"))
    print("gallery   : %d photo(s)" % len(entry["gallery"]))
    print("excerpt   : %s" % entry["excerpt"])
    print("words     : %d" % word_count)
    print("published : %s" % entry["published"])
    for w in warnings:
        print("  ! %s" % w)

    if args.dry_run:
        print("\nDRY-RUN: nothing was written.")
        return

    feed["posts"] = [entry] + posts
    with open(FEED_PATH, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(feed, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    print("\nAdded to data/feed.json as %s." % ("PUBLISHED" if args.publish else "a DRAFT"))
    print("Next: python generate_sitemaps.py   then commit & push.")
    if not args.publish:
        print("Publish it from /admin when the text is ready.")


if __name__ == "__main__":
    main()
