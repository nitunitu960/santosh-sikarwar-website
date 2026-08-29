// ============================================================
// article.js — progressive enhancement for PRE-RENDERED article
// pages at /samachar/<slug>/. The article content and all SEO
// metadata are already in the static HTML; this script only adds
// interactivity: share buttons, photo-story lightbox, scroll UX,
// mobile nav, and brand sync. No content is fetched or rendered.
// ============================================================

function absImg(v) {
  if (!v) return "";
  if (/^https?:\/\//.test(v)) return v;
  if (v.charAt(0) === "/") return v;
  return "/images/" + v.replace(/^images\//, "");
}

// ---- Footer year ----
(function () {
  var y = document.getElementById("year");
  if (y) y.textContent = new Date().getFullYear();
})();

// ---- Share controls (Web Share API + copy link) ----
(function setupShare() {
  var url = (document.querySelector('link[rel="canonical"]') || {}).href || location.href;
  var title = document.title.replace(/\s*\|\s*Santosh Sikarwar\s*$/, "");

  var copyBtn = document.getElementById("share-copy");
  if (copyBtn) {
    copyBtn.addEventListener("click", async function () {
      try {
        await navigator.clipboard.writeText(url);
      } catch (e) {
        var ta = document.createElement("textarea");
        ta.value = url; document.body.appendChild(ta); ta.select();
        try { document.execCommand("copy"); } catch (_) {}
        ta.remove();
      }
      var old = copyBtn.textContent;
      copyBtn.textContent = "लिंक कॉपी हो गया";
      copyBtn.classList.add("copied");
      setTimeout(function () { copyBtn.textContent = old; copyBtn.classList.remove("copied"); }, 1800);
    });
  }
  var nativeBtn = document.getElementById("share-native");
  if (nativeBtn && navigator.share) {
    nativeBtn.hidden = false;
    nativeBtn.addEventListener("click", function () {
      navigator.share({ title: title, url: url }).catch(function () {});
    });
  }
})();

// ---- Photo-story lightbox: prev/next, counter, keyboard, swipe ----
(function setupPhotoStory() {
  var figs = Array.prototype.slice.call(document.querySelectorAll(".gallery-item"));
  var lightbox = document.getElementById("lightbox");
  if (!lightbox || !figs.length) return;

  var items = figs.map(function (f) {
    return { src: f.getAttribute("data-src"), caption: f.getAttribute("data-caption") || "" };
  });
  var lbImg = document.getElementById("lightbox-img");
  var lbCap = document.getElementById("lightbox-caption");
  var counter = document.getElementById("lightbox-counter");
  var prevBtn = document.getElementById("lightbox-prev");
  var nextBtn = document.getElementById("lightbox-next");
  var closeBtn = lightbox.querySelector(".lightbox-close");
  var many = items.length > 1;
  var idx = 0;

  function show(i) {
    idx = (i + items.length) % items.length;
    var it = items[idx];
    lbImg.src = absImg(it.src);
    lbImg.alt = it.caption ? "संतोष सिकरवार - " + it.caption : "संतोष सिकरवार - कार्यक्रम फ़ोटो";
    lbCap.textContent = it.caption || "";
    if (counter) { counter.hidden = !many; counter.textContent = (idx + 1) + " / " + items.length; }
    if (prevBtn) prevBtn.hidden = !many;
    if (nextBtn) nextBtn.hidden = !many;
  }
  function open(i) { show(i); lightbox.classList.add("open"); lightbox.setAttribute("aria-hidden", "false"); }
  function close() { lightbox.classList.remove("open"); lightbox.setAttribute("aria-hidden", "true"); }

  figs.forEach(function (fig, i) {
    fig.addEventListener("click", function () { open(i); });
    fig.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open(i); }
    });
  });

  if (prevBtn) prevBtn.addEventListener("click", function (e) { e.stopPropagation(); show(idx - 1); });
  if (nextBtn) nextBtn.addEventListener("click", function (e) { e.stopPropagation(); show(idx + 1); });
  if (closeBtn) closeBtn.addEventListener("click", close);
  lightbox.addEventListener("click", function (e) { if (e.target === lightbox) close(); });
  document.addEventListener("keydown", function (e) {
    if (!lightbox.classList.contains("open")) return;
    if (e.key === "Escape") close();
    else if (many && e.key === "ArrowLeft") show(idx - 1);
    else if (many && e.key === "ArrowRight") show(idx + 1);
  });

  var sx = 0;
  lightbox.addEventListener("touchstart", function (e) { sx = e.changedTouches[0].clientX; }, { passive: true });
  lightbox.addEventListener("touchend", function (e) {
    var dx = e.changedTouches[0].clientX - sx;
    if (many && Math.abs(dx) > 45) show(idx + (dx < 0 ? 1 : -1));
  }, { passive: true });
})();

// ---- Scroll progress + sticky nav + back-to-top ----
(function scrollUX() {
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var bar = document.getElementById("scroll-progress");
  var toTop = document.getElementById("to-top");
  var header = document.querySelector(".site-header");
  if (toTop) toTop.removeAttribute("hidden");
  var ticking = false;
  function update() {
    ticking = false;
    var st = window.pageYOffset || document.documentElement.scrollTop;
    var h = (document.documentElement.scrollHeight - document.documentElement.clientHeight) || 1;
    if (bar) bar.style.width = Math.min(100, (st / h) * 100) + "%";
    if (toTop) toTop.classList.toggle("show", st >= 500);
    if (header) header.classList.toggle("scrolled", st > 40);
  }
  function onScroll() { if (!ticking) { ticking = true; requestAnimationFrame(update); } }
  window.addEventListener("scroll", onScroll, { passive: true });
  update();
  if (toTop) toTop.addEventListener("click", function () {
    window.scrollTo({ top: 0, behavior: reduce ? "auto" : "smooth" });
  });
})();

// ---- Mobile nav toggle ----
(function navToggle() {
  var toggle = document.querySelector(".nav-toggle");
  var links = document.querySelector(".nav-links");
  if (!toggle || !links) return;
  toggle.addEventListener("click", function () {
    var open = links.classList.toggle("open");
    toggle.setAttribute("aria-expanded", String(open));
  });
  links.querySelectorAll("a").forEach(function (a) {
    a.addEventListener("click", function () {
      links.classList.remove("open");
      toggle.setAttribute("aria-expanded", "false");
    });
  });
})();

// ---- Header logo + favicon from settings (keeps sync with admin) ----
(async function brand() {
  try {
    var res = await fetch("/data/settings.json", { cache: "no-store" });
    if (!res.ok) return;
    var s = await res.json();
    if (s.logo) { var el = document.getElementById("site-logo"); if (el) el.src = s.logo; }
    var fav = document.querySelector('link[rel="icon"]');
    if (fav && (s.favicon || s.logo)) { fav.href = s.favicon || s.logo; fav.removeAttribute("type"); }
  } catch (e) {}
})();
