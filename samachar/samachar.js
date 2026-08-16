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

  // Group by year
  const groups = {};
  list.forEach((x) => {
    const y = (/(\d{4})/.exec(x.post.date || "") || [])[1] || "अन्य";
    (groups[y] = groups[y] || []).push(x);
  });
  const years = Object.keys(groups).sort((a, b) => b.localeCompare(a));

  let html = '<h1 class="section-title" style="text-align:left">समाचार एवं गतिविधियाँ</h1>';
  years.forEach((y) => {
    html += `<h2 class="archive-year">${escapeHtml(y)}</h2>`;
    html += '<div class="feed-grid">' + groups[y].map(renderCard).join("") + "</div>";
  });
  c.innerHTML = html;
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

  // Article body
  const metaLine = [formatHindiDate(post.date), post.location, post.category]
    .filter(Boolean).map(escapeHtml).join(" · ");
  const feature = post.image
    ? `<img class="article-hero" src="${absImg(post.image)}" alt="${escapeHtml(post.title)}" fetchpriority="high" decoding="async" />`
    : "";
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
      ${feature}
      <div class="article-body">${bodyToHtml(post.text)}</div>
      ${gallery}
      <p class="article-back"><a href="/samachar/">← समाचार सूची</a> · <a href="/">मुख्य पृष्ठ</a></p>
    </article>
    ${relatedHtml}`;

  setupLightbox();
}

function setupLightbox() {
  const lightbox = document.getElementById("lightbox");
  if (!lightbox) return;
  const lbImg = document.getElementById("lightbox-img");
  const lbCap = document.getElementById("lightbox-caption");
  const open = (el) => {
    lbImg.src = el.dataset.src;
    lbImg.alt = el.dataset.caption || "संतोष सिकरवार - फ़ोटो";
    lbCap.textContent = el.dataset.caption || "";
    lightbox.classList.add("open");
    lightbox.setAttribute("aria-hidden", "false");
  };
  document.querySelectorAll(".gallery-item").forEach((fig) => {
    fig.addEventListener("click", () => open(fig));
    fig.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open(fig); } });
  });
  const close = () => { lightbox.classList.remove("open"); lightbox.setAttribute("aria-hidden", "true"); };
  lightbox.querySelector(".lightbox-close").addEventListener("click", close);
  lightbox.addEventListener("click", (e) => { if (e.target === lightbox) close(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") close(); });
}

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
