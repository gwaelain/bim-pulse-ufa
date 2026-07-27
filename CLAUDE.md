# CLAUDE.md — BIM Pulse Ufa

Памятка для работы над сайтом **[bim-pulse.ru](https://bim-pulse.ru)**.
Статический сайт про BIM, AI и автоматизацию проектирования. Чистый HTML/CSS/JS
без фреймворков и сборщика. Хостинг — **GitHub Pages** (ветка `main`, папка `/root`,
домен через `CNAME`). **Пуш в `main` = деплой** — пушить только по явной команде.

## Структура

**Страницы (правятся вручную)**
- `index.html` + лендинги: `services`, `cases`, `blog`, `contacts`,
  `ai-in-bim`, `revit-automation`, `dynamo-scripts`, `bim-coordination`.
- `404.html` — страница ошибки. `article.html` — legacy-рендер статьи по `?slug=`.

**Статьи (генерируются, вручную НЕ править)**
- `<slug>.html` собираются из `news.js`. Правишь `news.js` → пересобираешь.

**Единый источник — партиалы** `tools/partials/`
- `header.html`, `footer.html`, `metrika.html` (Yandex.Metrika).
- Меняешь навигацию/подвал/аналитику → правишь ОДИН партиал и запускаешь
  `python3 tools/apply_shell.py` (проставит во все страницы).

**Стили** — грузятся во всех страницах в порядке: `style.css` → (точечный) → `global.css`.
- `style.css` — основной; `global.css` грузится последним и побеждает в каскаде.
- Точечные: `blog/cases/contacts/services.css` и `article.css` (для 4 лендингов-статей).

**Изображения** — WebP для контента, `og-image.jpg` для соц-превью,
`favicon.png` (32), `apple-touch-icon.png` (180), `logo.png`.

## Частые задачи

**Добавить/изменить статью**
1. Правь объект в `news.js` (`slug`, `title`, `excerpt`, `date`, `image`, `content`).
2. Собери: `bash tools/build.sh` (нужен node + python3, кросс-платформенно) — перезапишет `<slug>.html`, обновит `sitemap.xml`.
3. Проверь ссылки: `python3 tools/check_links.py`.

**Изменить шапку/подвал/аналитику** — правь `tools/partials/*`, затем `python3 tools/apply_shell.py`.

## Проверять перед коммитом

- **Баланс скобок в CSS** — раньше уже был баг: незакрытая `{` уводила весь хвост
  правил на уровень глубже, и с нативным CSS-nesting Chrome молча игнорировал их.
  Быстрая проверка: `python3 -c "s=open('article.css').read();print(s.count('{'),s.count('}'))"` — числа должны совпадать.
- **Ссылки**: `python3 tools/check_links.py`.
- **Визуально** через headless Chrome (стили ссылок/тёмный фон легко ломаются молча):
  ```
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless \
    --disable-gpu --window-size=1280,2400 --screenshot=out.png \
    "file://$PWD/ai-in-bim.html"
  ```
  Для вычисленного стиля элемента — временная страница с `getComputedStyle` + скриншот.

## Правила

- Все `.md` — на русском, кратко, для новичка, с инструкциями.
- НЕ править сгенерированные `<slug>.html` вручную — только через `news.js` + `build.sh`.
- НЕ коммитить сразу: сначала `git diff`, дождаться подтверждения. Коммитить только нужные файлы.
- Пуш в `main` публикует сайт — только по явной команде.
- НЕ коммитить секреты/ключи.
