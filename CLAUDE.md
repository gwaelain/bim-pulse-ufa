# CLAUDE.md — BIM Pulse Ufa

Памятка для работы над сайтом **[bim-pulse.ru](https://bim-pulse.ru)**.
Статический сайт про BIM, AI и автоматизацию проектирования. Чистый HTML/CSS/JS
без фреймворков и сборщика.

## ⚠️ Где сайт живёт на самом деле (главное)

Домен **не** обслуживается GitHub Pages, хотя Pages в репозитории включён.
DNS ведёт на **наш сервер 5.188.27.237** (NS у Cloudflare, A → 5.188.27.237),
раздаёт **Caddy**: `bim-pulse.ru { root * /srv/bim-pulse-ufa }`,
том `/opt/static:/srv:ro` — то есть файлы лежат в `/opt/static/bim-pulse-ufa`.

**Пуш в GitHub сайт НЕ обновляет.** Деплой — скриптом с локальной машины:

```powershell
e:\Project\infra\scripts\deploy-bim-pulse.ps1        # залить + пересобрать
e:\Project\infra\scripts\deploy-bim-pulse.ps1 -SkipDrip
```

(Раньше на сервере был cron `git pull` каждые 2 минуты — он падал с TLS-ошибкой,
и сайт полтора месяца стоял на старой версии. Cron заменён на ежедневный `drip.sh`.)

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
`5 7 * * * /opt/static/bim-pulse-ufa/tools/drip.sh` — раз в сутки пересобирает сайт,
публикует статьи, у которых наступил `publish_at`, и пингует IndexNow.
Поэтому сервер должен получать не только html, но и `content/` + `tools/`
(deploy-скрипт это делает).

Очередь публикаций заполняется из черновиков:
`python e:\Project\_content\tools\zapolnit-ochered.py --projekt bim-pulse --start 2026-08-14`

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
