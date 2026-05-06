const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => document.querySelectorAll(selector);

const filters = ["Все", "BIM", "AI", "Data", "Infrastructure", "Revit", "Coordination", "Automation"];
let activeFilter = "Все";

function renderFilters() {
  const holder = $("#filters");
  if (!holder) return;
  holder.innerHTML = filters.map(f => `<button class="filter ${f === activeFilter ? "active" : ""}" data-filter="${f}">${f}</button>`).join("");
  $$(".filter").forEach(btn => btn.addEventListener("click", () => {
    activeFilter = btn.dataset.filter;
    renderFilters();
    renderNews();
  }));
}

function renderNews() {
  const grid = $("#newsGrid");
  if (!grid || !window.NEWS) return;
  const items = activeFilter === "Все" ? window.NEWS : window.NEWS.filter(item => item.category === activeFilter);
  grid.innerHTML = items.map(item => `
    <a class="news-card" href="article.html?slug=${item.slug}">
      <img src="${item.image}" alt="${item.title}" loading="lazy" />
      <div>
        <div class="meta"><span>${item.category}</span><span>${item.date}</span></div>
        <h3>${item.title}</h3>
        <p>${item.excerpt}</p>
        <b>Читать →</b>
      </div>
    </a>
  `).join("");
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
    <img class="article-cover" src="${item.image}" alt="${item.title}" />
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
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) entry.target.classList.add("visible");
    });
  }, { threshold: 0.15 });
  $$(".reveal").forEach(el => observer.observe(el));
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

renderFilters();
renderNews();
renderArticle();
initReveal();
initModals();
