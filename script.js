// ============================================================
// Google Analytics 4 (GA4)
// ------------------------------------------------------------
// अपनी GA4 Measurement ID यहाँ डालें (जैसे "G-XXXXXXXXXX")।
// खाली रहने पर Analytics लोड नहीं होगा (कोई फ़र्ज़ी ID नहीं)।
// विवरण: README.md देखें।
// ============================================================
const GA_MEASUREMENT_ID = ""; // <-- अपनी असली GA4 ID यहाँ डालें

function initAnalytics() {
  if (!GA_MEASUREMENT_ID) return; // no ID set -> skip
  const s = document.createElement("script");
  s.async = true;
  s.src = "https://www.googletagmanager.com/gtag/js?id=" + GA_MEASUREMENT_ID;
  document.head.appendChild(s);
  window.dataLayer = window.dataLayer || [];
  window.gtag = function () { window.dataLayer.push(arguments); };
  window.gtag("js", new Date());
  window.gtag("config", GA_MEASUREMENT_ID);
}

// Safe event helper (no-op if GA not configured)
function trackEvent(name, params) {
  if (typeof window.gtag === "function") window.gtag("event", name, params || {});
}
initAnalytics();

// ===== Mobile nav toggle =====
const toggle = document.querySelector(".nav-toggle");
const links = document.querySelector(".nav-links");

toggle.addEventListener("click", () => {
  const open = links.classList.toggle("open");
  toggle.setAttribute("aria-expanded", String(open));
});

links.querySelectorAll("a").forEach((link) => {
  link.addEventListener("click", () => {
    links.classList.remove("open");
    toggle.setAttribute("aria-expanded", "false");
  });
});

// ===== Current year in footer =====
document.getElementById("year").textContent = new Date().getFullYear();

// Branded placeholder shown when a photo file is missing
const PLACEHOLDER =
  "data:image/svg+xml;charset=utf-8," +
  encodeURIComponent(
    '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400">' +
      '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">' +
      '<stop offset="0" stop-color="#ff9933"/><stop offset="1" stop-color="#138808"/>' +
      "</linearGradient></defs>" +
      '<rect width="400" height="400" fill="url(#g)"/>' +
      '<text x="50%" y="54%" font-size="30" fill="#fff" text-anchor="middle" font-family="sans-serif">फ़ोटो जोड़ें</text>' +
      "</svg>"
  );

function withFallback(alt) {
  return `onerror="this.onerror=null;this.src='${PLACEHOLDER}';" alt="${alt}"`;
}

// Normalize an image path (handles "/images/x.jpg", "images/x.jpg" or "x.jpg")
function imgSrc(v) {
  if (!v) return "";
  let s = v.replace(/^\//, ""); // strip leading slash
  if (!s.startsWith("images/")) s = "images/" + s;
  return s;
}

// Load a JSON file; returns null if it can't be loaded (e.g. local file:// preview)
async function loadJSON(path) {
  try {
    const res = await fetch(path, { cache: "no-store" });
    if (!res.ok) return null;
    return await res.json();
  } catch (e) {
    return null;
  }
}

// ===== Render everything =====
(async function init() {
  await renderSettings();
  await renderFeed();
  await renderGallery();
  renderLatestStrip();
  setupVCard();
})();

// ---- Live "नवीनतम गतिविधि" strip (most recent published, by date) ----
async function renderLatestStrip() {
  const strip = document.getElementById("latest-strip");
  if (!strip) return;
  const data = await loadJSON("data/feed.json");
  const pub = data && data.posts
    ? data.posts.map((post, idx) => ({ post, idx })).filter((x) => x.post.published !== false)
    : [];
  if (!pub.length) { strip.hidden = true; return; }
  pub.sort((a, b) => String(b.post.date || "").localeCompare(String(a.post.date || "")));
  const { post, idx } = pub[0];
  const meta = [formatHindiDate(post.date), post.location].filter(Boolean).join(" · ");
  const txt = document.getElementById("latest-text");
  if (txt) txt.textContent = (meta ? meta + " — " : "") + post.title;
  strip.setAttribute("href", articleUrl(post, idx));
  strip.hidden = false;
}

// ---- Digital profile: vCard "Add to Contacts" (real data only) ----
async function setupVCard() {
  const btn = document.getElementById("vcard-btn");
  if (!btn) return;
  const s = (await loadJSON("data/settings.json")) || {};
  const isPlaceholder = (v) => !v || /0{4,}|example|info@santoshsikarwar\.in/i.test(v);
  btn.addEventListener("click", () => {
    const lines = ["BEGIN:VCARD", "VERSION:3.0", "N:Sikarwar;Santosh;;;", "FN:" + (s.name || "संतोष सिकरवार")];
    if (s.role) lines.push("TITLE:" + s.role);
    lines.push("ORG:Bharatiya Janata Party, Agra");
    lines.push("URL:https://santoshsikarwar.in/");
    if (!isPlaceholder(s.phone)) lines.push("TEL;TYPE=CELL:" + s.phone.replace(/\s/g, ""));
    if (!isPlaceholder(s.email)) lines.push("EMAIL:" + s.email);
    if (s.area) lines.push("ADR;TYPE=WORK:;;;" + s.area + ";;;India");
    [s.facebook, s.instagram, s.twitter].filter(Boolean).forEach((u) => lines.push("X-SOCIALPROFILE:" + u));
    lines.push("END:VCARD");
    const blob = new Blob([lines.join("\r\n")], { type: "text/vcard;charset=utf-8" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "santosh-sikarwar.vcf";
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
    trackEvent("contact_click", { method: "vcard" });
  });
}

// ===== Scroll progress + back-to-top =====
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

// ===== Active nav highlighting + reveal-on-scroll =====
(function navAndReveal() {
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const supportsIO = "IntersectionObserver" in window;

  if (!reduce && supportsIO) {
    const blocks = document.querySelectorAll("main .section, .banner, .tl-item");
    blocks.forEach((b) => b.classList.add("reveal"));
    const io = new IntersectionObserver((entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
      });
    }, { threshold: 0.12 });
    blocks.forEach((b) => io.observe(b));
  }

  const navLinks = Array.prototype.slice.call(document.querySelectorAll(".nav-links a"));
  const map = {};
  navLinks.forEach((a) => {
    const href = a.getAttribute("href");
    if (href && href.charAt(0) === "#") map[href.slice(1)] = a;
  });
  const ids = Object.keys(map);
  if (ids.length && supportsIO) {
    const spy = new IntersectionObserver((entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) {
          navLinks.forEach((a) => a.classList.remove("active"));
          if (map[e.target.id]) map[e.target.id].classList.add("active");
        }
      });
    }, { rootMargin: "-45% 0px -50% 0px" });
    ids.forEach((id) => { const el = document.getElementById(id); if (el) spy.observe(el); });
  }
})();

// ---- Settings: hero photo + contact details ----
async function renderSettings() {
  const s = await loadJSON("data/settings.json");
  if (!s) return;

  if (s.photo) {
    const frame = document.getElementById("hero-photo-frame");
    if (frame) {
      const heroAlt = `${s.name || "संतोष सिकरवार"} - ${s.role || "जिला उपाध्यक्ष, भाजपा आगरा"}`;
      frame.innerHTML =
        `<img class="hero-img" src="${imgSrc(s.photo)}" alt="${heroAlt}" width="300" height="375" fetchpriority="high" decoding="async" onerror="this.onerror=null;this.src='${PLACEHOLDER}';" />`;
    }
  }

  // Patriotic banner (wide photo)
  const banner = document.getElementById("banner");
  if (banner && s.banner) {
    banner.style.backgroundImage = `url('${imgSrc(s.banner)}')`;
    banner.hidden = false;
    banner.setAttribute("role", "img");
    banner.setAttribute(
      "aria-label",
      s.bannerCaption || `${s.name || "संतोष सिकरवार"} - ${s.role || ""}`
    );
    const cap = document.getElementById("banner-caption");
    if (cap) cap.textContent = s.bannerCaption || "";
  }
  // Contact: show only real values; hide placeholder email/phone entirely
  const isPlaceholderContact = (v) => !v || /0{4,}|example|info@santoshsikarwar\.in/i.test(v);
  const email = document.getElementById("c-email");
  const phone = document.getElementById("c-phone");
  const area = document.getElementById("c-area");
  const hideLi = (el) => { const li = el && el.closest("li"); if (li) li.hidden = true; };
  if (email) {
    if (isPlaceholderContact(s.email)) { hideLi(email); }
    else {
      email.textContent = s.email;
      email.href = "mailto:" + s.email;
      email.addEventListener("click", () => trackEvent("contact_click", { method: "email" }));
    }
  }
  if (phone) {
    if (isPlaceholderContact(s.phone)) { hideLi(phone); }
    else {
      phone.textContent = s.phone;
      phone.href = "tel:" + s.phone.replace(/\s/g, "");
      phone.addEventListener("click", () => trackEvent("phone_click", { method: "phone" }));
    }
  }
  if (area && s.area) { area.textContent = s.area; }

  // Social links: set href from settings, hide any that are empty
  const socials = { facebook: s.facebook, instagram: s.instagram, twitter: s.twitter };
  document.querySelectorAll("#social-links a[data-social]").forEach((a) => {
    const url = socials[a.dataset.social];
    if (url) {
      a.href = url;
      a.hidden = false;
      a.addEventListener("click", () =>
        trackEvent("social_profile_click", { network: a.dataset.social })
      );
    } else {
      a.hidden = true;
    }
  });
}

// ---- Shared content helpers (used by homepage + /samachar/) ----
const HINDI_MONTHS = ["जनवरी","फ़रवरी","मार्च","अप्रैल","मई","जून","जुलाई","अगस्त","सितंबर","अक्टूबर","नवंबर","दिसंबर"];
function formatHindiDate(d) {
  if (!d) return "";
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(d);
  if (m) return parseInt(m[3], 10) + " " + HINDI_MONTHS[parseInt(m[2], 10) - 1] + " " + m[1];
  return d; // already a display string (backward compatible)
}
function escapeHtml(s) {
  return String(s || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}
function postExcerpt(post) {
  if (post.excerpt) return post.excerpt;
  const t = (post.text || "").replace(/\s+/g, " ").trim();
  return t.length > 140 ? t.slice(0, 140) + "…" : t;
}
function articleUrl(post, idx) {
  return post.slug ? "/samachar/?slug=" + encodeURIComponent(post.slug) : "/samachar/?id=" + idx;
}
// Return published posts (with original index kept), newest first, featured prioritized
function publishedPosts(data) {
  if (!data || !data.posts) return null;
  const list = data.posts
    .map((post, idx) => ({ post, idx }))
    .filter((x) => x.post.published !== false);
  list.sort((a, b) => {
    if (!!b.post.featured !== !!a.post.featured) return b.post.featured ? 1 : -1;
    return String(b.post.date || "").localeCompare(String(a.post.date || ""));
  });
  return list;
}

// ---- Homepage activity feed (latest published) ----
async function renderFeed() {
  const grid = document.getElementById("feed-grid");
  if (!grid) return;
  const data = await loadJSON("data/feed.json");
  const list = publishedPosts(data);

  if (!list) {
    grid.innerHTML = '<p class="empty-note">समाचार लोड करने के लिए वेबसाइट को ऑनलाइन (लाइव) देखें।</p>';
    return;
  }
  if (!list.length) {
    grid.innerHTML = '<p class="empty-note">अभी कोई अपडेट नहीं है।</p>';
    return;
  }

  grid.innerHTML = list.slice(0, 6).map(({ post, idx }) => {
    const href = articleUrl(post, idx);
    const img = post.image
      ? `<div class="feed-img"><img src="${imgSrc(post.image)}" ${withFallback(escapeHtml(post.title))} loading="lazy" /></div>`
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
  }).join("");

  grid.querySelectorAll(".feed-card").forEach((a) =>
    a.addEventListener("click", () => trackEvent("news_article_open", { url: a.getAttribute("href") }))
  );
}

// ---- Gallery + lightbox ----
async function renderGallery() {
  const grid = document.getElementById("gallery-grid");
  if (!grid) return;
  const data = await loadJSON("data/gallery.json");
  const photos = data && data.photos ? data.photos : null;

  if (!photos) {
    grid.innerHTML = '<p class="empty-note">गैलरी देखने के लिए वेबसाइट को ऑनलाइन (लाइव) देखें।</p>';
    return;
  }
  if (!photos.length) {
    grid.innerHTML = '<p class="empty-note">अभी कोई फ़ोटो नहीं है।</p>';
    return;
  }

  grid.innerHTML = photos.map((item) => `
    <figure class="gallery-item" data-src="${imgSrc(item.src)}" data-caption="${item.caption || ""}">
      <img src="${imgSrc(item.src)}" ${withFallback(item.caption ? "संतोष सिकरवार - " + item.caption : "संतोष सिकरवार - कार्यक्रम फ़ोटो")} loading="lazy" />
      ${item.caption ? `<figcaption>${item.caption}</figcaption>` : ""}
    </figure>`).join("");

  const lightbox = document.getElementById("lightbox");
  const lbImg = document.getElementById("lightbox-img");
  const lbCap = document.getElementById("lightbox-caption");

  grid.querySelectorAll(".gallery-item").forEach((fig) => {
    fig.addEventListener("click", () => {
      lbImg.src = fig.dataset.src;
      lbImg.alt = fig.dataset.caption || "संतोष सिकरवार - फ़ोटो";
      lbCap.textContent = fig.dataset.caption;
      lightbox.classList.add("open");
      lightbox.setAttribute("aria-hidden", "false");
      trackEvent("gallery_open", { caption: fig.dataset.caption || "" });
    });
  });

  const close = () => {
    lightbox.classList.remove("open");
    lightbox.setAttribute("aria-hidden", "true");
  };
  lightbox.querySelector(".lightbox-close").addEventListener("click", close);
  lightbox.addEventListener("click", (e) => { if (e.target === lightbox) close(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") close(); });
}
