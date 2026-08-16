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
})();

// ---- Settings: hero photo + contact details ----
async function renderSettings() {
  const s = await loadJSON("data/settings.json");
  if (!s) return;

  if (s.photo) {
    const frame = document.getElementById("hero-photo-frame");
    if (frame) {
      frame.innerHTML =
        `<img class="hero-img" src="${imgSrc(s.photo)}" ${withFallback(s.name || "फ़ोटो")} />`;
    }
  }
  const email = document.getElementById("c-email");
  const phone = document.getElementById("c-phone");
  const area = document.getElementById("c-area");
  if (email && s.email) { email.textContent = s.email; email.href = "mailto:" + s.email; }
  if (phone && s.phone) { phone.textContent = s.phone; phone.href = "tel:" + s.phone.replace(/\s/g, ""); }
  if (area && s.area) { area.textContent = s.area; }

  // Social links: set href from settings, hide any that are empty
  const socials = { facebook: s.facebook, instagram: s.instagram, twitter: s.twitter };
  document.querySelectorAll("#social-links a[data-social]").forEach((a) => {
    const url = socials[a.dataset.social];
    if (url) { a.href = url; a.hidden = false; }
    else { a.hidden = true; }
  });
}

// ---- Daily feed ----
async function renderFeed() {
  const grid = document.getElementById("feed-grid");
  if (!grid) return;
  const data = await loadJSON("data/feed.json");
  const posts = data && data.posts ? data.posts : null;

  if (!posts) {
    grid.innerHTML = '<p class="empty-note">समाचार लोड करने के लिए वेबसाइट को ऑनलाइन (लाइव) देखें।</p>';
    return;
  }
  if (!posts.length) {
    grid.innerHTML = '<p class="empty-note">अभी कोई अपडेट नहीं है।</p>';
    return;
  }

  grid.innerHTML = posts.map((post) => {
    const img = post.image
      ? `<div class="feed-img"><img src="${imgSrc(post.image)}" ${withFallback(post.title)} loading="lazy" /></div>`
      : "";
    return `
      <article class="feed-card">
        ${img}
        <div class="feed-body">
          <span class="feed-date">${post.date || ""}</span>
          <h3>${post.title || ""}</h3>
          <p>${post.text || ""}</p>
        </div>
      </article>`;
  }).join("");
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
      <img src="${imgSrc(item.src)}" ${withFallback(item.caption || "फ़ोटो")} loading="lazy" />
      ${item.caption ? `<figcaption>${item.caption}</figcaption>` : ""}
    </figure>`).join("");

  const lightbox = document.getElementById("lightbox");
  const lbImg = document.getElementById("lightbox-img");
  const lbCap = document.getElementById("lightbox-caption");

  grid.querySelectorAll(".gallery-item").forEach((fig) => {
    fig.addEventListener("click", () => {
      lbImg.src = fig.dataset.src;
      lbCap.textContent = fig.dataset.caption;
      lightbox.classList.add("open");
      lightbox.setAttribute("aria-hidden", "false");
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
