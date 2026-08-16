// ============================================================
// समाचार / गतिविधियाँ — archive + single-article viewer
// Reads /data/feed.json. Shows one article when ?slug= or ?id=
// is present, otherwise the full archive. No external libraries.
// ============================================================

const SITE = "https://santoshsikarwar.in";
const HINDI_MONTHS = ["जनवरी","फ़रवरी","मार्च","अप्रैल","मई","जून","जुलाई","अगस्त","सितंबर","अक्टूबर","नवंबर","दिसंबर"];

function formatHindiDate(d) {
  if (!d) return "";
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(d);
  if (m) return parseInt(m[3], 10) + " " + HINDI_MONTHS[parseInt(m[2], 10) - 1] + " " + m[1];
  return d;
}
function escapeHtml(s) {
  return String(s || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}
function absImg(v) {
  if (!v) return "";
  if (/^https?:\/\//.test(v)) return v;
  if (v.charAt(0) === "/") return v;
  return "/images/" + v.replace(/^images\//, "");
}
function postExcerpt(post) {
  if (post.excerpt) return post.excerpt;
  const t = (post.text || "").replace(/\s+/g, " ").trim();
  return t.length > 160 ? t.slice(0, 160) + "…" : t;
}
function articleUrl(post, idx) {
  return post.slug ? "/samachar/?slug=" + encodeURIComponent(post.slug) : "/samachar/?id=" + idx;
}
function bodyToHtml(text) {
  return String(text || "")
    .split(/\n{2,}/)
    .map((p) => "<p>" + escapeHtml(p).replace(/\n/g, "<br>") + "</p>")
    .join("");
}

async function loadFeed() {
  try {
    const res = await fetch("/data/feed.json", { cache: "no-store" });
    if (!res.ok) return null;
    return await res.json();
  } catch (e) {
    return null;
  }
}

function publishedList(data) {
  return data.posts
    .map((post, idx) => ({ post, idx }))
    .filter((x) => x.post.published !== false)
    .sort((a, b) => String(b.post.date || "").localeCompare(String(a.post.date || "")));
}

function setMeta(id, attr, value) {
  const el = document.getElementById(id);
  if (el) el.setAttribute(attr, value);
}

function renderCard({ post, idx }) {
  const href = articleUrl(post, idx);
  const img = post.image
    ? `<div class="feed-img"><img src="${absImg(post.image)}" alt="${escapeHtml(post.title)}" loading="lazy" /></div>`
    : "";
  const meta = [post.category, post.location].filter(Boolean).map(escapeHtml).join(" · ");
  return `
    <a class="feed-card" href="${href}" aria-label="${escapeHtml(post.title)}">
      ${img}
      <div class="feed-body">
        <span class="feed-date">${formatHindiDate(post.date)}</span>
        ${meta ? `<span class="feed-meta">${meta}</span>` : ""}
        <h3>${escapeHtml(post.title)}</h3>
        <p>${escapeHtml(postExcerpt(post))}</p>
        <span class="read-more">और पढ़ें →</span>
      </div>
    </a>`;
}

function renderArchive(list) {
  const c = document.getElementById("samachar-content");
  document.getElementById("breadcrumb").innerHTML =
    '<a href="/">मुख्य पृष्ठ</a> <span>›</span> <span>समाचार</span>';

  if (!list.length) {
    c.innerHTML = '<h1 class="section-title" style="text-align:left">समाचार एवं गतिविधियाँ</h1><p class="empty-note">अभी कोई प्रकाशित गतिविधि नहीं है।</p>';
    return;
  }

  const cats = Array.from(new Set(list.map((x) => x.post.category).filter(Boolean)));
  const years = Array.from(new Set(list.map((x) => (/(\d{4})/.exec(x.post.date || "") || [])[1]).filter(Boolean)))
    .sort((a, b) => b.localeCompare(a));

  c.innerHTML = `
    <h1 class="section-title" style="text-align:left">समाचार एवं गतिविधियाँ</h1>
    <div class="news-controls">
      <input type="search" id="news-search" class="news-search" placeholder="खोजें… (शीर्षक, स्थान, श्रेणी)" aria-label="समाचार खोजें" />
      <div class="filter-row" id="cat-filters" role="group" aria-label="श्रेणी फ़िल्टर">
        <button type="button" class="chip-btn active" data-cat="all">सभी</button>
        ${cats.map((cat) => `<button type="button" class="chip-btn" data-cat="${escapeHtml(cat)}">${escapeHtml(cat)}</button>`).join("")}
      </div>
      ${years.length > 1 ? `<div class="filter-row" id="year-filters" role="group" aria-label="वर्ष फ़िल्टर">
        <button type="button" class="chip-btn active" data-year="all">सभी वर्ष</button>
        ${years.map((y) => `<button type="button" class="chip-btn" data-year="${y}">${y}</button>`).join("")}
      </div>` : ""}
    </div>
    <div id="news-results" class="feed-grid"></div>
    <p class="empty-note" id="news-empty" hidden>कोई परिणाम नहीं मिला</p>`;

  const results = document.getElementById("news-results");
  const empty = document.getElementById("news-empty");
  let curCat = "all", curYear = "all", curQ = "";

  function apply() {
    const q = curQ.trim().toLowerCase();
    const filtered = list.filter(({ post }) => {
      if (curCat !== "all" && post.category !== curCat) return false;
      const y = (/(\d{4})/.exec(post.date || "") || [])[1] || "";
      if (curYear !== "all" && y !== curYear) return false;
      if (q) {
        const hay = [post.title, post.excerpt, post.text, post.location, post.category]
          .filter(Boolean).join(" ").toLowerCase();
        if (hay.indexOf(q) === -1) return false;
      }
      return true;
    });
    results.innerHTML = filtered.map(renderCard).join("");
    empty.hidden = filtered.length > 0;
  }
  apply();

  c.querySelectorAll("#cat-filters .chip-btn").forEach((b) =>
    b.addEventListener("click", () => {
      c.querySelectorAll("#cat-filters .chip-btn").forEach((x) => x.classList.remove("active"));
      b.classList.add("active"); curCat = b.dataset.cat; apply();
    })
  );
  const yf = document.getElementById("year-filters");
  if (yf) yf.querySelectorAll(".chip-btn").forEach((b) =>
    b.addEventListener("click", () => {
      yf.querySelectorAll(".chip-btn").forEach((x) => x.classList.remove("active"));
      b.classList.add("active"); curYear = b.dataset.year; apply();
    })
  );
  const search = document.getElementById("news-search");
  let t;
  search.addEventListener("input", () => { clearTimeout(t); t = setTimeout(() => { curQ = search.value; apply(); }, 200); });
}

function renderArticle(entry, list) {
  const { post, idx } = entry;
  const c = document.getElementById("samachar-content");
  const url = SITE + articleUrl(post, idx);
  const img = post.image ? absImg(post.image) : "/images/og-image.jpg";
  const imgAbs = /^https?:/.test(img) ? img : SITE + img;
  const desc = postExcerpt(post);

  // Breadcrumb
  document.getElementById("breadcrumb").innerHTML =
    '<a href="/">मुख्य पृष्ठ</a> <span>›</span> <a href="/samachar/">समाचार</a> <span>›</span> <span>' +
    escapeHtml(post.title) + "</span>";

  // Meta / title
  document.title = post.title + " | Santosh Sikarwar";
  setMeta("canonical-link", "href", url);
  const md = document.querySelector('meta[name="description"]');
  if (md) md.setAttribute("content", desc);
  setMeta("og-type", "content", "article");
  setMeta("og-title", "content", post.title);
  setMeta("og-desc", "content", desc);
  setMeta("og-url", "content", url);
  setMeta("og-image", "content", imgAbs);
  setMeta("tw-title", "content", post.title);
  setMeta("tw-desc", "content", desc);
  setMeta("tw-image", "content", imgAbs);

  // NewsArticle JSON-LD
  const ld = {
    "@context": "https://schema.org",
    "@type": "NewsArticle",
    "headline": post.title,
    "description": desc,
    "image": [imgAbs],
    "datePublished": post.date || undefined,
    "dateModified": post.updated_at || post.date || undefined,
    "articleSection": post.category || undefined,
    "inLanguage": "hi-IN",
    "author": { "@type": "Person", "name": post.author || "संतोष सिकरवार" },
    "publisher": {
      "@type": "Organization",
      "name": "Santosh Sikarwar",
      "logo": { "@type": "ImageObject", "url": SITE + "/images/santosh-sikarwar.jpg" }
    },
    "about": { "@type": "Person", "@id": SITE + "/#person", "name": "Santosh Sikarwar" },
    "mainEntityOfPage": { "@type": "WebPage", "@id": url }
  };
  document.getElementById("article-jsonld").textContent = JSON.stringify(ld);

  // Reading time (from actual words)
  const words = (post.text || "").trim().split(/\s+/).filter(Boolean).length;
  const readMin = Math.max(1, Math.round(words / 200));

  // Article body
  const metaLine = [formatHindiDate(post.date), post.location, post.category, readMin + " मिनट पढ़ने का समय"]
    .filter(Boolean).map(escapeHtml).join(" · ");
  const feature = post.image
    ? `<img class="article-hero" src="${absImg(post.image)}" alt="${escapeHtml(post.title)}" fetchpriority="high" decoding="async" />`
    : "";

  // Share bar
  const enc = encodeURIComponent(url);
  const encT = encodeURIComponent(post.title);
  const shareHtml = `
    <div class="share-bar" aria-label="साझा करें">
      <span class="share-label">साझा करें:</span>
      <a class="share-btn wa" href="https://wa.me/?text=${encT}%20${enc}" target="_blank" rel="noopener">WhatsApp</a>
      <a class="share-btn fb" href="https://www.facebook.com/sharer/sharer.php?u=${enc}" target="_blank" rel="noopener">Facebook</a>
      <a class="share-btn xx" href="https://twitter.com/intent/tweet?text=${encT}&url=${enc}" target="_blank" rel="noopener">X</a>
      <button type="button" class="share-btn copy" id="share-copy">लिंक कॉपी</button>
      <button type="button" class="share-btn native" id="share-native" hidden>Share</button>
    </div>`;
  const gallery = Array.isArray(post.gallery) && post.gallery.length
    ? `<div class="gallery-grid article-gallery">` +
      post.gallery.map((g) =>
        `<figure class="gallery-item" data-src="${absImg(g.src)}" data-caption="${escapeHtml(g.caption || "")}" tabindex="0" role="button" aria-label="${escapeHtml(g.caption || "फ़ोटो")}">
          <img src="${absImg(g.src)}" alt="${escapeHtml(g.caption ? "संतोष सिकरवार - " + g.caption : "संतोष सिकरवार - कार्यक्रम फ़ोटो")}" loading="lazy" />
          ${g.caption ? `<figcaption>${escapeHtml(g.caption)}</figcaption>` : ""}
        </figure>`).join("") +
      `</div>`
    : "";

  // Related (same category, else latest), exclude current
  const related = list
    .filter((x) => x.idx !== idx)
    .sort((a, b) => {
      const ac = a.post.category === post.category ? 0 : 1;
      const bc = b.post.category === post.category ? 0 : 1;
      if (ac !== bc) return ac - bc;
      return String(b.post.date || "").localeCompare(String(a.post.date || ""));
    })
    .slice(0, 3);
  const relatedHtml = related.length
    ? `<section class="related"><h2 class="section-title" style="text-align:left">संबंधित गतिविधियाँ</h2>
        <div class="feed-grid">${related.map(renderCard).join("")}</div></section>`
    : "";

  c.innerHTML = `
    <article class="article">
      <h1>${escapeHtml(post.title)}</h1>
      <p class="article-meta">${metaLine}${post.author ? " · " + escapeHtml(post.author) : ""}</p>
      ${shareHtml}
      ${feature}
      <div class="article-body">${bodyToHtml(post.text)}</div>
      ${gallery}
      <p class="article-back"><a href="/samachar/">← समाचार सूची</a> · <a href="/">मुख्य पृष्ठ</a></p>
    </article>
    ${relatedHtml}`;

  setupShare(url, post.title);
  setupPhotoStory(Array.isArray(post.gallery) ? post.gallery : []);
}

// ---- Share controls (Web Share API + copy link) ----
function setupShare(url, title) {
  const copyBtn = document.getElementById("share-copy");
  if (copyBtn) {
    copyBtn.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(url);
      } catch (e) {
        const ta = document.createElement("textarea");
        ta.value = url; document.body.appendChild(ta); ta.select();
        try { document.execCommand("copy"); } catch (_) {}
        ta.remove();
      }
      const old = copyBtn.textContent;
      copyBtn.textContent = "लिंक कॉपी हो गया";
      copyBtn.classList.add("copied");
      setTimeout(() => { copyBtn.textContent = old; copyBtn.classList.remove("copied"); }, 1800);
    });
  }
  const nativeBtn = document.getElementById("share-native");
  if (nativeBtn && navigator.share) {
    nativeBtn.hidden = false;
    nativeBtn.addEventListener("click", () => {
      navigator.share({ title: title, url: url }).catch(() => {});
    });
  }
}

// ---- Photo-story lightbox: prev/next, counter, keyboard, swipe ----
function setupPhotoStory(items) {
  const lightbox = document.getElementById("lightbox");
  if (!lightbox) return;
  const lbImg = document.getElementById("lightbox-img");
  const lbCap = document.getElementById("lightbox-caption");
  const counter = document.getElementById("lightbox-counter");
  const prevBtn = document.getElementById("lightbox-prev");
  const nextBtn = document.getElementById("lightbox-next");
  const closeBtn = lightbox.querySelector(".lightbox-close");
  const many = items.length > 1;
  let idx = 0;

  function show(i) {
    idx = (i + items.length) % items.length;
    const it = items[idx];
    lbImg.src = absImg(it.src);
    lbImg.alt = it.caption ? "संतोष सिकरवार - " + it.caption : "संतोष सिकरवार - कार्यक्रम फ़ोटो";
    lbCap.textContent = it.caption || "";
    if (counter) { counter.hidden = !many; counter.textContent = (idx + 1) + " / " + items.length; }
    if (prevBtn) prevBtn.hidden = !many;
    if (nextBtn) nextBtn.hidden = !many;
  }
  function open(i) { show(i); lightbox.classList.add("open"); lightbox.setAttribute("aria-hidden", "false"); }
  function close() { lightbox.classList.remove("open"); lightbox.setAttribute("aria-hidden", "true"); }

  document.querySelectorAll(".gallery-item").forEach((fig, i) => {
    fig.addEventListener("click", () => open(i));
    fig.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open(i); } });
  });

  if (prevBtn) prevBtn.addEventListener("click", (e) => { e.stopPropagation(); show(idx - 1); });
  if (nextBtn) nextBtn.addEventListener("click", (e) => { e.stopPropagation(); show(idx + 1); });
  if (closeBtn) closeBtn.addEventListener("click", close);
  lightbox.addEventListener("click", (e) => { if (e.target === lightbox) close(); });
  document.addEventListener("keydown", (e) => {
    if (!lightbox.classList.contains("open")) return;
    if (e.key === "Escape") close();
    else if (many && e.key === "ArrowLeft") show(idx - 1);
    else if (many && e.key === "ArrowRight") show(idx + 1);
  });

  // Touch swipe
  let sx = 0;
  lightbox.addEventListener("touchstart", (e) => { sx = e.changedTouches[0].clientX; }, { passive: true });
  lightbox.addEventListener("touchend", (e) => {
    const dx = e.changedTouches[0].clientX - sx;
    if (many && Math.abs(dx) > 45) show(idx + (dx < 0 ? 1 : -1));
  }, { passive: true });
}

// ---- Scroll progress + back-to-top (samachar pages) ----
(function scrollUX() {
  const bar = document.getElementById("scroll-progress");
  const toTop = document.getElementById("to-top");
  function onScroll() {
    const st = document.documentElement.scrollTop || document.body.scrollTop;
    const h = (document.documentElement.scrollHeight - document.documentElement.clientHeight) || 1;
    if (bar) bar.style.width = Math.min(100, (st / h) * 100) + "%";
    if (toTop) toTop.hidden = st < 500;
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();
  if (toTop) toTop.addEventListener("click", () => window.scrollTo({ top: 0, behavior: "smooth" }));
})();

(async function init() {
  const y = document.getElementById("year");
  if (y) y.textContent = new Date().getFullYear();

  const data = await loadFeed();
  const content = document.getElementById("samachar-content");
  if (!data || !data.posts) {
    content.innerHTML = '<h1 class="section-title" style="text-align:left">समाचार एवं गतिविधियाँ</h1><p class="empty-note">सामग्री लोड नहीं हो पाई। कृपया बाद में पुनः प्रयास करें।</p>';
    return;
  }

  const list = publishedList(data);
  const params = new URLSearchParams(location.search);
  const slug = params.get("slug");
  const id = params.get("id");

  let entry = null;
  if (slug) entry = list.find((x) => x.post.slug === slug) || null;
  else if (id !== null) entry = list.find((x) => String(x.idx) === String(id)) || null;

  if ((slug || id !== null) && entry) {
    renderArticle(entry, list);
  } else if (slug || id !== null) {
    // Requested article not found or unpublished -> show archive
    renderArchive(list);
  } else {
    renderArchive(list);
  }
})();
