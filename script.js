document.documentElement.classList.add('js');
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => document.querySelectorAll(selector);

let activeFilter = "Все";

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function renderNewsGrid() {
  const grid = $("#newsGrid");
  if (!grid || !window.NEWS) return;
  grid.innerHTML = window.NEWS.map(item => `
    <a class="news-card" href="${escapeHtml(item.slug)}.html" data-category="${escapeHtml(item.category)}">
      <img src="${escapeHtml(item.image)}" alt="${escapeHtml(item.title)}" loading="lazy" onerror="this.src='bim-model-1.webp'" />
      <div>
        <div class="meta"><span>${escapeHtml(item.category)}</span><span>${escapeHtml(item.date)}</span></div>
        <h3>${escapeHtml(item.title)}</h3>
        <p>${escapeHtml(item.excerpt)}</p>
        <b>Читать →</b>
      </div>
    </a>
  `).join("");
}

function initFilters() {
  const holder = $("#filters");
  const grid = $("#newsGrid");
  if (!holder || !grid) return;
  holder.addEventListener("click", (event) => {
    const btn = event.target.closest(".filter");
    if (!btn) return;
    activeFilter = btn.dataset.filter;
    $$(".filter").forEach(item => item.classList.toggle("active", item === btn));
    $$(".news-card").forEach(card => {
      const show = activeFilter === "Все" || card.dataset.category === activeFilter;
      card.style.display = show ? "flex" : "none";
    });
  });
}

const RU_MONTHS = {
  "января": "01", "февраля": "02", "марта": "03", "апреля": "04",
  "мая": "05", "июня": "06", "июля": "07", "августа": "08",
  "сентября": "09", "октября": "10", "ноября": "11", "декабря": "12"
};

function ruDateToIso(date) {
  const m = String(date).match(/(\d{1,2})\s+([а-яё]+)\s+(\d{4})/i);
  if (!m || !RU_MONTHS[m[2].toLowerCase()]) return null;
  return `${m[3]}-${RU_MONTHS[m[2].toLowerCase()]}-${m[1].padStart(2, "0")}`;
}

function setMeta(attr, key, content) {
  let el = document.head.querySelector(`meta[${attr}="${key}"]`);
  if (!el) { el = document.createElement("meta"); el.setAttribute(attr, key); document.head.appendChild(el); }
  el.setAttribute("content", content);
}

function setCanonical(href) {
  let el = document.head.querySelector('link[rel="canonical"]');
  if (!el) { el = document.createElement("link"); el.rel = "canonical"; document.head.appendChild(el); }
  el.setAttribute("href", href);
}

function setJsonLd(obj) {
  let el = document.getElementById("article-jsonld");
  if (!el) { el = document.createElement("script"); el.type = "application/ld+json"; el.id = "article-jsonld"; document.head.appendChild(el); }
  el.textContent = JSON.stringify(obj);
}

// Per-article SEO: заголовок, description, canonical, OG/Twitter и JSON-LD
// проставляются из данных статьи (news.js). Google рендерит JS и читает их;
// для соц-скрейперов без JS остаётся статический брендовый fallback в <head>.
function updateArticleMeta(item) {
  const OG = "https://bim-pulse.ru/og-image.jpg";
  const url = `https://bim-pulse.ru/${item.slug}.html`;
  const title = `${item.title} — BIM Pulse Ufa`;
  const desc = item.excerpt;
  const iso = ruDateToIso(item.date);

  document.title = title;
  setMeta("name", "description", desc);
  setCanonical(url);
  setMeta("property", "og:type", "article");
  setMeta("property", "og:title", title);
  setMeta("property", "og:description", desc);
  setMeta("property", "og:url", url);
  setMeta("property", "og:image", OG);
  setMeta("property", "og:site_name", "BIM Pulse Ufa");
  setMeta("name", "twitter:card", "summary_large_image");
  setMeta("name", "twitter:title", title);
  setMeta("name", "twitter:description", desc);
  setMeta("name", "twitter:image", OG);

  setJsonLd({
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": item.title,
    "description": desc,
    "image": `https://bim-pulse.ru/${item.image}`,
    "author": { "@type": "Organization", "name": "BIM Pulse Ufa" },
    "publisher": {
      "@type": "Organization",
      "name": "BIM Pulse Ufa",
      "logo": { "@type": "ImageObject", "url": "https://bim-pulse.ru/logo.png" }
    },
    ...(iso ? { "datePublished": iso, "dateModified": iso } : {}),
    "mainEntityOfPage": { "@type": "WebPage", "@id": url }
  });
}

function renderArticle() {
  const target = $("#articleFull");
  if (!target || !window.NEWS) return;
  const slug = new URLSearchParams(window.location.search).get("slug");
  const item = window.NEWS.find(article => article.slug === slug) || window.NEWS[0];
  updateArticleMeta(item);
  target.innerHTML = `
    <div class="meta"><span>${item.category}</span><span>${item.date}</span></div>
    <h1>${item.title}</h1>
    <p class="lead">${item.excerpt}</p>
    <img class="article-cover" src="${item.image}" alt="${item.title}" onerror="this.src='bim-model-1.webp'" />
    ${item.content.map(p => `<p>${p}</p>`).join("")}
    <div class="article-cta">
      <h3>Нужен похожий BIM/AI процесс?</h3>
      <p>Напишите в Telegram или на email — разберём задачу и предложим архитектуру решения.</p>
      <a class="btn primary" href="https://t.me/bim_pulse_ufa" target="_blank" rel="noreferrer">Telegram</a>
      <a class="btn secondary" href="mailto:im@laingawe.ru">Email</a>
    </div>
  `;
}

function initReveal() {
  const items = $$(".reveal");
  if (!('IntersectionObserver' in window)) {
    items.forEach(el => el.classList.add("visible"));
    return;
  }
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add("visible");
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.08 });
  items.forEach(el => observer.observe(el));
}

function initModals() {
  const modal = $("#modal");
  const content = $("#modalContent");
  const close = $("#modalClose");
  if (!modal || !content || !close) return;
  const data = {
    "case-1": "<p class='eyebrow'>Кейс</p><h2>Координация модели</h2><p>Настройка регулярных проверок, классификация коллизий и отчёты для смежников. Результат — меньше критических ошибок до выпуска документации.</p>",
    "case-2": "<p class='eyebrow'>Кейс</p><h2>Автоматизация Revit</h2><p>Dynamo-сценарии для параметров, спецификаций и выгрузок. Результат — меньше ручной работы и чище данные для BIM-дашборда.</p>"
  };
  $$('[data-modal]').forEach(card => card.addEventListener('click', () => {
    content.innerHTML = data[card.dataset.modal];
    modal.classList.add('open');
  }));
  close.addEventListener('click', () => modal.classList.remove('open'));
  modal.addEventListener('click', (e) => { if (e.target === modal) modal.classList.remove('open'); });
}

renderNewsGrid();
initFilters();
renderArticle();
initReveal();
initModals();
