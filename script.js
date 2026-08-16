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
      '<text x="50%" y="46%" font-size="90" text-anchor="middle">\uD83E\uDEB7</text>' +
      '<text x="50%" y="64%" font-size="26" fill="#fff" text-anchor="middle" font-family="sans-serif">फ़ोटो जोड़ें</text>' +
      "</svg>"
  );

function withFallback(alt) {
  return `onerror="this.onerror=null;this.src='${PLACEHOLDER}';" alt="${alt}"`;
}

// ===== Render Daily Feed (from data/feed.js) =====
(function renderFeed() {
  const grid = document.getElementById("feed-grid");
  if (!grid || typeof FEED_DATA === "undefined") return;

  if (!FEED_DATA.length) {
    grid.innerHTML = '<p class="empty-note">अभी कोई अपडेट नहीं है।</p>';
    return;
  }

  grid.innerHTML = FEED_DATA.map((post) => {
    const img = post.image
      ? `<div class="feed-img"><img src="images/${post.image}" ${withFallback(post.title)} loading="lazy" /></div>`
      : "";
    return `
      <article class="feed-card">
        ${img}
        <div class="feed-body">
          <span class="feed-date">${post.date}</span>
          <h3>${post.title}</h3>
          <p>${post.text}</p>
        </div>
      </article>`;
  }).join("");
})();

// ===== Render Photo Gallery (from data/gallery.js) =====
(function renderGallery() {
  const grid = document.getElementById("gallery-grid");
  if (!grid || typeof GALLERY_DATA === "undefined") return;

  if (!GALLERY_DATA.length) {
    grid.innerHTML = '<p class="empty-note">अभी कोई फ़ोटो नहीं है।</p>';
    return;
  }

  grid.innerHTML = GALLERY_DATA.map((item) => `
    <figure class="gallery-item" data-src="images/${item.src}" data-caption="${item.caption || ""}">
      <img src="images/${item.src}" ${withFallback(item.caption || "फ़ोटो")} loading="lazy" />
      ${item.caption ? `<figcaption>${item.caption}</figcaption>` : ""}
    </figure>`).join("");

  // Lightbox
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
  lightbox.addEventListener("click", (e) => {
    if (e.target === lightbox) close();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") close();
  });
})();
