const glow = document.getElementById('cursorGlow');
window.addEventListener('pointermove', (e) => {
  if (!glow) return;
  glow.style.left = `${e.clientX}px`;
  glow.style.top = `${e.clientY}px`;
});

const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.15 });

document.querySelectorAll('.reveal').forEach((el) => observer.observe(el));

const countObserver = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (!entry.isIntersecting) return;
    const el = entry.target;
    const target = Number(el.dataset.count || 0);
    const prefix = el.dataset.prefix || '';
    const suffix = el.dataset.suffix || '';
    let current = 0;
    const step = Math.max(1, Math.ceil(target / 42));
    const timer = setInterval(() => {
      current += step;
      if (current >= target) {
        current = target;
        clearInterval(timer);
      }
      el.textContent = `${prefix}${current}${suffix}`;
    }, 24);
    countObserver.unobserve(el);
  });
}, { threshold: 0.5 });

document.querySelectorAll('[data-count]').forEach((el) => countObserver.observe(el));

const newsList = document.getElementById('newsList');
if (newsList && Array.isArray(window.BIM_NEWS)) {
  newsList.innerHTML = window.BIM_NEWS.map((item) => `
    <article class="media-card reveal">
      <div>
        <small>${item.category} · ${item.date}</small>
        <h3>${item.title}</h3>
        <p>${item.description}</p>
      </div>
      <a href="${item.url}">${item.cta}</a>
    </article>
  `).join('');
  document.querySelectorAll('.media-card.reveal').forEach((el) => observer.observe(el));
}
