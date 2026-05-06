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
    <a class="news-card" href="article.html?slug=${escapeHtml(item.slug)}" data-category="${escapeHtml(item.category)}">
      <img src="${escapeHtml(item.image)}" alt="${escapeHtml(item.title)}" loading="lazy" onerror="this.src='bim-model-1.png'" />
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

function renderArticle() {
  const target = $("#articleFull");
  if (!target || !window.NEWS) return;
  const slug = new URLSearchParams(window.location.search).get("slug");
  const item = window.NEWS.find(article => article.slug === slug) || window.NEWS[0];
  document.title = `${item.title} — BIM Pulse Ufa`;
  target.innerHTML = `
    <div class="meta"><span>${item.category}</span><span>${item.date}</span></div>
    <h1>${item.title}</h1>
    <p class="lead">${item.excerpt}</p>
    <img class="article-cover" src="${item.image}" alt="${item.title}" onerror="this.src='bim-model-1.png'" />
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
