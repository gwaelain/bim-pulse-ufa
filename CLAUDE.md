# CLAUDE.md — BIM Pulse Ufa

Памятка для работы над сайтом **[bim-pulse.ru](https://bim-pulse.ru)**.
Статический сайт про BIM, AI и автоматизацию проектирования. Чистый HTML/CSS/JS
без фреймворков и сборщика.

## ⚠️ Где сайт живёт на самом деле (главное)

Домен **не** обслуживается GitHub Pages, хотя Pages в репозитории включён.
DNS ведёт на **наш сервер 5.188.27.237** (NS у Cloudflare, A → 5.188.27.237),
раздаёт **Caddy**: `bim-pulse.ru { root * /srv/bim-pulse-ufa }`,
том `/opt/static:/srv:ro` — то есть файлы лежат в `/opt/static/bim-pulse-ufa`.

**Сайт обновляется из гита** (с 15.08.2026): на сервере лежит клон репозитория
`/opt/drip/bim-pulse-ufa`, скрипт `/opt/drip/bimpulse-publish.sh` по cron (`5 7` ежедневно
и `*/10` — подхват свежих пушей) делает `git fetch` → сборку → `rsync` в
`/opt/static/bim-pulse-ufa` → IndexNow → коммит и пуш обратно. Доступ к приватному
репозиторию — по deploy-ключу (`/root/.ssh/bimpulse_deploy`, SSH через `ssh.github.com:443`,
алиас `github-bimpulse` в `/root/.ssh/config`).

Ручная заливка `infra\scripts\deploy-bim-pulse.ps1` (pscp) — запасной путь, если GitHub
недоступен; после неё всё равно нужен пуш, иначе сервер затрёт правки своей версией.

## ⚠️ Правило: работаем только через git, и всегда сначала подтягиваем

`origin/main` регулярно уходит вперёд твоей копии — сервер сам публикует статьи и пушит
результат. Правка «вслепую» кончается конфликтом при пуше или работой со старыми данными
(типичный симптом: в `published.json` статьи нет, а на сайте она уже открывается).

**Перед любой правкой:** `infra\scripts\sync-saity.ps1` — подтянет оба сайта
(репозиторий с незакоммиченными правками пропустит, чтобы ничего не потерять).
Вручную: `git fetch origin && git reset --hard origin/main`.

**Как выкатывать:** правишь исходники → коммит → `git push`. Через 10 минут сервер подхватит сам.

**Руками не редактировать** (перезапишется при сборке): `<slug>.html`, `news.js`,
`sitemap.xml`, `tools/published.json`, блоки между `<!-- articles:auto -->`,
`<!-- services:auto -->`, `<!-- latest:auto -->`.

## Статьи: единственный источник — markdown

`content/articles/<slug>.md` — фронтматтер + текст. Всё остальное генерируется:

```
python tools/gen_articles.py        # страницы + news.js + blog.html + sitemap.xml
python tools/gen_articles.py --all  # собрать и те, чья дата ещё не наступила
python tools/check_links.py         # проверка внутренних ссылок
```

Фронтматтер:

```yaml
---
title: до 65 знаков
slug: имя-файла
description: 150-160 знаков
category: Dynamo | Revit | Coordination | Data | AI
keywords: [5-7 ключей]
publish_at: 2026-08-14      # до этой даты страницы не существует (капельная публикация)
updated_at: 2026-08-13      # необязательно, идёт в lastmod и JSON-LD
---
```

`news.js` теперь **генерируется** — руками не править, как и `<slug>.html`.

**Капельная публикация:** на сервере крутится
`/opt/drip/bimpulse-publish.sh` — тянет свежий код из гита, публикует статьи,
у которых наступил `publish_at`, раскладывает статику и пингует IndexNow.

Очередь публикаций заполняется из черновиков:
`python e:\Project\_content\tools\zapolnit-ochered.py --projekt bim-pulse --start 2026-08-14`

## Страницы услуг

`content/services/<slug>.md` → `<slug>.html` в корне, собирает `tools/gen_services.py`
(вызывается из `gen_articles.py`, отдельно запускать не нужно).

Отличия от статей: приоритет 0.9 в sitemap, JSON-LD `Service` + `BreadcrumbList` + `FAQPage`,
блок «Другие услуги», CTA на Telegram и форму. Ссылки на них вставляются в `services.html`
между маркерами `<!-- services:auto -->`.

Фронтматтер: `title` (до 60 знаков), `slug`, `description` (150–160), `h1`, `lead`,
`keywords`, необязательные `service_type` и `updated_at`.

Темы выбраны по разбору рынка `_content\_klyuchi\RYNOK-2026-08-14.md` — там же данные о том,
по каким запросам сайт уже показывается (Google: «автоматизация проверки bim моделей»,
«bim автоматизация api»; Яндекс: Dynamo и массовые операции в Revit).

## Что где лежит

- Страницы, которые правятся руками: `index`, `services`, `cases`, `about`, `blog`,
  `faq`, `contacts`, плюс лендинги `ai-in-bim`, `revit-automation`, `dynamo-scripts`,
  `bim-coordination`. `404.html`, `article.html` (legacy-рендер по `?slug=`).
- Партиалы `tools/partials/` — `header.html`, `footer.html`, `metrika.html`.
  Правишь один → `python tools/apply_shell.py` разносит по страницам,
  затем `python tools/gen_articles.py` (статьи берут партиалы при сборке).
- Стили: `style.css` → точечные (`article.css` и др.) → `global.css` (грузится
  последним и побеждает; типографика лонгридов — в нём).
- Картинки: WebP для контента, `og-image.jpg`, `favicon.png`, `apple-touch-icon.png`.

## SEO-обвязка (сделано, не сломать)

- Яндекс.Вебмастер: хост подтверждён мета-тегом `yandex-verification` в `index.html`
  (аккаунт аналитики портфеля, `infra\scripts\yandex-webmaster.ps1`), sitemap отправлен.
- Google Search Console: подтверждение файлом `googlebd1c94cea8b05eef.html` в корне,
  скрипт `infra\gsc\verify_file.py`.
- Яндекс.Метрика 109103460 — в партиале `tools/partials/metrika.html`.
- IndexNow: ключ-файл `5ce63dcf399ad423cb6f435df02501d4.txt` в корне + `tools/indexnow.py`.
- В каждой статье: JSON-LD `Article` + `BreadcrumbList`, canonical, OG, хлебные крошки,
  блок «Читайте дальше» (перелинковка по категории).

## Проверять перед деплоем

- `python tools/check_links.py` — битые внутренние ссылки.
- **Баланс скобок в CSS**: `python -c "s=open('global.css',encoding='utf-8').read();print(s.count('{'),s.count('}'))"`.
  Незакрытая `{` из-за нативного CSS-nesting молча уводит весь хвост правил.
- Тексты статей — через ворота `e:\Project\dzen-lab\engine\readability.py` и `mashinnost.py`
  (правила живого текста: `e:\Project\_content\BRIEF-ZHIVOY-TEKST.md`).

## Правила

- Все `.md` — на русском, кратко, с инструкциями.
- Не править сгенерированное: `<slug>.html`, `news.js`, блоки между `<!-- articles:auto -->`.
- Секреты не коммитить. Пароль сервера и токены — только из сейфа.
