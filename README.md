# BIM Pulse Ufa

Статический сайт **[bim-pulse.ru](https://bim-pulse.ru)** — BIM, AI и автоматизация
проектирования. Чистый HTML/CSS/JS без фреймворков. Хостинг — **GitHub Pages**
(ветка `main`, папка `/root`, кастомный домен через `CNAME`).

## Как устроено

**Страницы**
- `index.html` + лендинги: `services`, `cases`, `blog`, `contacts`,
  `ai-in-bim`, `revit-automation`, `dynamo-scripts`, `bim-coordination` —
  уникальный контент, правится вручную.
- Статьи: `<slug>.html` — **генерируются** из `news.js` (не править вручную).
- `404.html` — кастомная страница ошибки. `article.html` — legacy-рендер статьи по `?slug=`.

**Единый источник (партиалы)** — `tools/partials/`
- `header.html`, `footer.html` — шапка/подвал (одинаковы на всех страницах).
- `metrika.html` — счётчик Yandex.Metrika.

Меняешь навигацию/подвал/аналитику — правишь **один** партиал и запускаешь
`python3 tools/apply_shell.py` (проставит во все страницы).

**Стили** — `style.css` (основной) + `global.css` (грузится последним, побеждает).
Есть точечные `blog/cases/contacts/services.css` и `article.css` (4 лендинга).
Все страницы грузят `style.css` + `global.css`.

**Изображения** — WebP для контента, `og-image.jpg` для соц-превью,
`favicon.png` (32) / `apple-touch-icon.png` (180), `logo.png` — бренд.

## Частые задачи

**Добавить/изменить статью**
1. Открой `news.js`, добавь/поменяй объект (`slug`, `title`, `excerpt`,
   `date`, `image`, `content`).
2. Сгенерируй страницы: `bash tools/build.sh` (нужен node + python3, кросс-платформенно).
   Перезапишет `<slug>.html`, обновит `sitemap.xml`.
3. Проверь ссылки: `python3 tools/check_links.py`.

**Изменить шапку/подвал/аналитику**
1. Правь `tools/partials/{header,footer,metrika}.html`.
2. `python3 tools/apply_shell.py` — проставит во все страницы.
3. `bash tools/build.sh` — синхронизирует сгенерированные статьи.

**Оптимизировать новое изображение**
- Контент → WebP: `sips -Z 1600 in.png --out /tmp/r.png && cwebp -q 82 /tmp/r.png -o out.webp`.
- CI не даст закоммитить картинку > 500 КБ.

**Предпросмотр локально**
```
python3 -m http.server 8137
# затем http://localhost:8137/index.html
```

## Инструменты (`tools/`)
- `gen_articles.py` — генератор страниц статей из `news.js`.
- `build.sh` — дамп `news.js` → JSON (JXA) + запуск генератора.
- `apply_shell.py` — проставляет партиалы (шапка/подвал/Metrika) во все страницы.
- `check_links.py` — офлайн-проверка внутренних ссылок.

## CI (`.github/workflows/`)
- `ci.yml` — на каждый push/PR: проверка внутренних ссылок + гард размера картинок.
- `links-external.yml` — еженедельно: проверка внешних ссылок (lychee).

## Деплой
Пуш в `main` → GitHub Pages пересобирает и публикует на `bim-pulse.ru`
(обычно < 1 минуты).

## Лицензия
Проприетарный проект, все права защищены — см. [`LICENSE`](LICENSE).
