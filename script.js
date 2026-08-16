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
  staggerReveal(Array.prototype.slice.call(document.querySelectorAll(".positions-list li")));
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

// ===== Scroll UX: progress bar, sticky nav, back-to-top, timeline illumination =====
(function scrollUX() {
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const bar = document.getElementById("scroll-progress");
  const toTop = document.getElementById("to-top");
  const header = document.querySelector(".site-header");
  const timeline = document.querySelector(".timeline");
  const tlItems = timeline ? Array.prototype.slice.call(timeline.querySelectorAll(".tl-item")) : [];
  if (toTop) toTop.removeAttribute("hidden");

  if (timeline && reduce) timeline.style.setProperty("--tl-progress", "100%");

  let ticking = false;
  function update() {
    ticking = false;
    const st = window.pageYOffset || document.documentElement.scrollTop;
    const h = (document.documentElement.scrollHeight - document.documentElement.clientHeight) || 1;
    if (bar) bar.style.width = Math.min(100, (st / h) * 100) + "%";
    if (toTop) toTop.classList.toggle("show", st >= 500);
    if (header) header.classList.toggle("scrolled", st > 40);

    if (timeline && !reduce) {
      const rect = timeline.getBoundingClientRect();
      const mid = window.innerHeight * 0.55;
      const total = rect.height || 1;
      const p = Math.max(0, Math.min(1, (mid - rect.top) / total));
      timeline.style.setProperty("--tl-progress", (p * 100).toFixed(1) + "%");
      let bestIdx = -1, bestDist = Infinity;
      tlItems.forEach((it, i) => {
        const top = it.getBoundingClientRect().top;
        if (top <= mid) { const d = mid - top; if (d < bestDist) { bestDist = d; bestIdx = i; } }
      });
      tlItems.forEach((it, i) => it.classList.toggle("tl-active", i === bestIdx));
    }
  }
  function onScroll() { if (!ticking) { ticking = true; requestAnimationFrame(update); } }
  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("resize", onScroll, { passive: true });
  update();
  if (toTop) toTop.addEventListener("click", () => window.scrollTo({ top: 0, behavior: reduce ? "auto" : "smooth" }));
})();

// ===== Subtle magnetic hero buttons (desktop, motion-safe) =====
(function magneticButtons() {
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const fine = window.matchMedia("(pointer: fine)").matches;
  if (reduce || !fine) return;
  document.querySelectorAll(".hero-actions .btn").forEach((btn) => {
    btn.addEventListener("pointermove", (e) => {
      const r = btn.getBoundingClientRect();
      const mx = e.clientX - (r.left + r.width / 2);
      const my = e.clientY - (r.top + r.height / 2);
      btn.style.transform = "translate(" + Math.max(-5, Math.min(5, mx * 0.15)) + "px," + Math.max(-5, Math.min(5, my * 0.15 - 2)) + "px)";
    });
    btn.addEventListener("pointerleave", () => { btn.style.transform = ""; });
  });
})();

// ===== Staggered reveal for injected items =====
function staggerReveal(items) {
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduce || !("IntersectionObserver" in window) || !items.length) return;
  items.forEach((el, i) => { el.classList.add("r-item"); el.style.transitionDelay = Math.min(i, 6) * 80 + "ms"; });
  const io = new IntersectionObserver((es) => {
    es.forEach((e) => { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } });
  }, { threshold: 0.1 });
  items.forEach((el) => io.observe(el));
}
function skeletonCards(n) {
  let h = "";
  for (let i = 0; i < n; i++) h += '<div class="skeleton-card"><div class="sk-img"></div><div class="sk-body"><div class="skeleton-line short"></div><div class="skeleton-line"></div><div class="skeleton-line"></div></div></div>';
  return h;
}

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

  // Custom logos (optional; fall back to default SVGs if empty)
  if (s.logo) {
    const v = imgSrc(s.logo);
    const hl = document.getElementById("site-logo"); if (hl) hl.src = v;
    const bl = document.getElementById("hero-lotus"); if (bl) bl.src = v;
  }
  // Favicon: dedicated field, else header logo, else default in HTML
  const favVal = s.favicon || s.logo;
  if (favVal) {
    const fav = document.getElementById("favicon");
    if (fav) { fav.href = "/" + imgSrc(favVal); fav.removeAttribute("type"); }
  }
  if (s.party_logo) {
    const pl = document.getElementById("party-logo"); if (pl) pl.src = imgSrc(s.party_logo);
  }
  // Timeline marker icon (CSS variable used by .tl-item::before)
  if (s.timeline_icon) {
    document.documentElement.style.setProperty("--tl-marker", "url('" + imgSrc(s.timeline_icon) + "')");
  }

  // Hero background photo (rally/flags) — shown blurred + tinted behind the hero.
  // Priority: CMS "hero_bg" setting, else auto-use images/hero-bg.jpg if present.
  function applyHeroBg(url) {
    const hero = document.querySelector(".hero-cine");
    if (!hero) return;
    hero.style.setProperty("--hero-bg-url", "url('" + url + "')");
    hero.classList.add("has-hero-bg");
  }
  if (s.hero_bg) {
    applyHeroBg(imgSrc(s.hero_bg));
  } else {
    const probe = new Image();
    probe.onload = () => applyHeroBg("images/hero-bg.jpg");
    probe.src = "images/hero-bg.jpg";
  }

  if (s.photo) {
    const frame = document.getElementById("hero-photo-frame");
    if (frame) {
      const heroAlt = `${s.name || "संतोष सिकरवार"} - ${s.role || "जिला उपाध्यक्ष, भाजपा आगरा"}`;
      frame.innerHTML =
        `<img class="hero-img" src="${imgSrc(s.photo)}" alt="${heroAlt}" width="300" height="375" fetchpriority="high" decoding="async" onerror="this.onerror=null;this.src='${PLACEHOLDER}';" />`;
    }
  }

  // Cutout portrait (transparent PNG) — shown frameless + blended into the hero.
  // Priority: CMS "photo_cutout", else auto-use images/hero-portrait.png if present.
  function applyCutout(url) {
    const hero = document.querySelector(".hero-cine");
    const frame = document.getElementById("hero-photo-frame");
    if (!hero || !frame) return;
    const heroAlt = `${s.name || "संतोष सिकरवार"} - ${s.role || "जिला उपाध्यक्ष, भाजपा आगरा"}`;
    frame.innerHTML =
      `<img class="hero-cutout" src="${url}" alt="${heroAlt}" decoding="async" fetchpriority="high" onerror="this.onerror=null;this.src='${PLACEHOLDER}';" />`;
    hero.classList.add("has-cutout");
  }
  if (s.photo_cutout) {
    applyCutout(imgSrc(s.photo_cutout));
  } else {
    const pc = new Image();
    pc.onload = () => applyCutout("images/hero-portrait.png");
    pc.src = "images/hero-portrait.png";
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
  grid.innerHTML = skeletonCards(3);
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
    const alt = escapeHtml(post.image_alt || post.title);
    const img = post.image
      ? `<div class="feed-img"><img src="${imgSrc(post.image)}" ${withFallback(alt)} loading="lazy" /></div>`
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
  staggerReveal(Array.prototype.slice.call(grid.querySelectorAll(".feed-card")));
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

  staggerReveal(Array.prototype.slice.call(grid.querySelectorAll(".gallery-item")));

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


// ============================================================
// Cinematic hero FX: parallax, mouse-light, exit, particle field
// ============================================================
(function heroFX() {
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const fine = window.matchMedia("(pointer: fine)").matches;
  const hero = document.querySelector(".hero-cine");
  if (!hero) return;

  // Parallax + mouse light (desktop, motion-safe)
  if (fine && !reduce) {
    const light = document.getElementById("fx-mouselight");
    const layers = hero.querySelectorAll("[data-depth]");
    hero.addEventListener("pointermove", (e) => {
      const r = hero.getBoundingClientRect();
      const x = (e.clientX - r.left) / r.width;
      const y = (e.clientY - r.top) / r.height;
      if (light) { light.style.setProperty("--mx", (x * 100) + "%"); light.style.setProperty("--my", (y * 100) + "%"); }
      const dx = x - 0.5, dy = y - 0.5;
      layers.forEach((l) => {
        const d = parseFloat(l.getAttribute("data-depth")) || 0;
        l.style.transform = "translate(" + (dx * -d).toFixed(2) + "px," + (dy * -d).toFixed(2) + "px)";
      });
    });
    hero.addEventListener("pointerleave", () => { layers.forEach((l) => (l.style.transform = "")); });
  }

  // Subtle scroll parallax (desktop, motion-safe): crowd down, portrait up, panel slight
  if (!reduce && fine) {
    const bg = document.getElementById("hero-bg");
    const photo = hero.querySelector(".hero-photo");
    const text = hero.querySelector(".hero-text");
    let t = false;
    window.addEventListener("scroll", () => {
      if (t) return; t = true;
      requestAnimationFrame(() => {
        t = false;
        const st = window.pageYOffset || document.documentElement.scrollTop;
        const p = Math.min(1, st / (window.innerHeight || 1));
        if (bg) bg.style.transform = "translateY(" + (p * 10).toFixed(1) + "px)";
        if (photo) photo.style.transform = "translateY(" + (-p * 8).toFixed(1) + "px)";
        if (text) text.style.transform = "translateY(" + (p * 4).toFixed(1) + "px)";
      });
    }, { passive: true });
  }

  // Particle field (skipped in the civic light theme where the canvas is hidden)
  const canvas = document.getElementById("fx-particles");
  if (!canvas || reduce || getComputedStyle(canvas).display === "none") return;
  const ctx = canvas.getContext("2d");
  const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
  const isMobile = window.innerWidth < 820;
  let W = 0, H = 0, parts = [], raf = null;
  let COUNT = isMobile ? 22 : 55;

  function resize() {
    W = hero.clientWidth; H = hero.clientHeight;
    canvas.width = W * dpr; canvas.height = H * dpr;
    canvas.style.width = W + "px"; canvas.style.height = H + "px";
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  function make() {
    parts = [];
    for (let i = 0; i < COUNT; i++) parts.push({ x: Math.random() * W, y: Math.random() * H, r: Math.random() * 1.8 + 0.6, vx: (Math.random() - 0.5) * 0.25, vy: (Math.random() - 0.5) * 0.25, a: Math.random() * 0.4 + 0.2 });
  }
  function step() {
    ctx.clearRect(0, 0, W, H);
    for (const p of parts) {
      p.x += p.vx; p.y += p.vy;
      if (p.x < 0) p.x = W; else if (p.x > W) p.x = 0;
      if (p.y < 0) p.y = H; else if (p.y > H) p.y = 0;
      ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, 6.283); ctx.fillStyle = "rgba(255,180,110," + p.a + ")"; ctx.fill();
    }
    if (!isMobile) {
      for (let i = 0; i < parts.length; i++) {
        for (let j = i + 1; j < parts.length; j++) {
          const a = parts[i], b = parts[j], ddx = a.x - b.x, ddy = a.y - b.y, d2 = ddx * ddx + ddy * ddy;
          if (d2 < 9000) { ctx.strokeStyle = "rgba(255,153,51," + (0.12 * (1 - d2 / 9000)).toFixed(3) + ")"; ctx.lineWidth = 0.5; ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke(); }
        }
      }
    }
    raf = requestAnimationFrame(step);
  }
  function start() { if (!raf) step(); }
  function stop() { if (raf) { cancelAnimationFrame(raf); raf = null; } }

  resize(); make(); start();
  window.addEventListener("resize", () => { resize(); make(); }, { passive: true });
  if ("IntersectionObserver" in window) {
    new IntersectionObserver((es) => { es.forEach((e) => { e.isIntersecting ? start() : stop(); }); }, { threshold: 0 }).observe(hero);
  }
})();

// ============================================================
// Desktop custom cursor (accent ring + dot; native cursor kept)
// ============================================================
(function customCursor() {
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const fine = window.matchMedia("(pointer: fine)").matches;
  if (reduce || !fine) return;
  const ring = document.getElementById("cursor-ring");
  const dot = document.getElementById("cursor-dot");
  if (!ring || !dot) return;
  document.body.classList.add("cursor-on");
  let rx = 0, ry = 0, tx = 0, ty = 0;
  window.addEventListener("pointermove", (e) => {
    tx = e.clientX; ty = e.clientY;
    dot.style.transform = "translate(" + tx + "px," + ty + "px) translate(-50%,-50%)";
  }, { passive: true });
  (function loop() {
    rx += (tx - rx) * 0.18; ry += (ty - ry) * 0.18;
    ring.style.transform = "translate(" + rx.toFixed(1) + "px," + ry.toFixed(1) + "px) translate(-50%,-50%)";
    requestAnimationFrame(loop);
  })();
  document.addEventListener("pointerover", (e) => {
    if (e.target.closest("a, button, .chip, .feed-card, .gallery-item, input")) ring.classList.add("hovering");
  });
  document.addEventListener("pointerout", (e) => {
    if (e.target.closest("a, button, .chip, .feed-card, .gallery-item, input")) ring.classList.remove("hovering");
  });
})();


// ============================================================
// Language toggle (Hindi / English) — swaps interface text
// Body/news content authored in Hindi remains as written.
// ============================================================
(function langToggle() {
  const btn = document.getElementById("lang-toggle");
  if (!btn) return;
  const nodes = document.querySelectorAll("[data-en]");
  // Preserve original Hindi (incl. inline HTML like <strong>) via a Map
  const originalHi = new Map();
  nodes.forEach((n) => originalHi.set(n, n.innerHTML));

  function apply(lang) {
    const en = lang === "en";
    nodes.forEach((n) => {
      const val = en ? n.getAttribute("data-en") : originalHi.get(n);
      // Fallback: never blank out content
      if (val != null && val !== "") n.innerHTML = val;
      else n.innerHTML = originalHi.get(n);
    });
    document.documentElement.lang = en ? "en" : "hi";
    btn.textContent = en ? "हिं" : "EN";
    btn.setAttribute("aria-label", en ? "हिंदी में बदलें" : "Switch to English");
    try { localStorage.setItem("ss_lang", lang); } catch (e) {}
  }

  let cur = "hi";
  try { if (localStorage.getItem("ss_lang") === "en") cur = "en"; } catch (e) {}
  apply(cur);
  btn.addEventListener("click", () => { cur = cur === "en" ? "hi" : "en"; apply(cur); });
})();


// ============================================================
// National Spirit section: reveal only if its photos actually load
// (avoids showing broken images if the files aren't uploaded yet)
// ============================================================
(function nationalSpirit() {
  const sec = document.getElementById("national-spirit");
  if (!sec) return;
  const imgs = ["ns-img-2", "ns-img-1"].map((id) => document.getElementById(id)).filter(Boolean);
  if (!imgs.length) return;
  let done = 0, ok = 0;
  const settle = (good) => {
    done++;
    if (good) ok++;
    if (done === imgs.length && ok > 0) sec.hidden = false;
  };
  imgs.forEach((im) => {
    if (im.complete) { settle(im.naturalWidth > 0); return; }
    im.addEventListener("load", () => settle(true));
    im.addEventListener("error", () => { const f = im.closest("figure"); if (f) f.remove(); settle(false); });
  });
})();
