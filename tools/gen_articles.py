#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сборка статей сайта из markdown-источников.

Источник правды — `content/articles/<slug>.md` (фронтматтер + markdown).
Раньше источником был `news.js`, теперь он наоборот генерируется отсюда.

Что делает:
  1. читает все .md, отбирает те, у кого `publish_at` <= сегодня (капельная публикация);
  2. рендерит `<slug>.html` в корне (шапка/подвал/Метрика из tools/partials);
  3. пишет `news.js` (window.NEWS) — им живут blog.html и index.html;
  4. вставляет статический список карточек в blog.html (между маркерами articles:auto),
     чтобы статьи видел поисковик, а не только браузер с JS;
  5. обновляет sitemap.xml с lastmod;
  6. складывает URL страниц, появившихся в этот запуск, в `tools/indexnow-new.txt`
     — их пингует drip.sh на сервере.

Запуск:  python3 tools/gen_articles.py [--all]
  --all  — игнорировать publish_at (собрать всё, для локального просмотра)
"""
from __future__ import annotations

import html
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from md import frontmatter, md_to_html, md_to_text  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "content" / "articles"
DOMAIN = "https://bim-pulse.ru"
SITE = "BIM Pulse Ufa"

HEADER = (ROOT / "tools/partials/header.html").read_text(encoding="utf-8").strip()
FOOTER = (ROOT / "tools/partials/footer.html").read_text(encoding="utf-8").strip()
YM = (ROOT / "tools/partials/metrika.html").read_text(encoding="utf-8").strip()

RU_MONTHS = ["января", "февраля", "марта", "апреля", "мая", "июня",
             "июля", "августа", "сентября", "октября", "ноября", "декабря"]
COVERS = ["Bim.webp", "Bim1.webp", "Bim2.webp", "bim-model-1.webp",
          "bim-model-2.webp", "bim-case-1.webp", "bim-case-2.webp"]


def ru_date(iso: str) -> str:
    d = datetime.strptime(iso, "%Y-%m-%d").date()
    return f"{d.day:02d} {RU_MONTHS[d.month - 1]} {d.year}"


def load() -> list[dict]:
    arts = []
    for f in sorted(SRC.glob("*.md")):
        meta, body = frontmatter(f.read_text(encoding="utf-8"))
        if not meta.get("slug"):
            meta["slug"] = f.stem
        meta.setdefault("publish_at", date.today().isoformat())
        meta.setdefault("category", "BIM")
        meta.setdefault("title", meta["slug"])
        text = md_to_text(body)
        meta.setdefault("description", text[:157].rsplit(" ", 1)[0] + "…")
        meta["_body"] = body
        meta["_words"] = len(text.split())
        meta.setdefault("image", COVERS[abs(hash(meta["slug"])) % len(COVERS)])
        arts.append(meta)
    arts.sort(key=lambda a: (a["publish_at"], a["slug"]), reverse=True)
    return arts


def faq_schema(body_html: str) -> dict | None:
    """Собирает FAQPage из блоков «**Вопрос?** ответ».

    Так копирайтеры оформляют мини-FAQ в конце статьи. Разметка FAQPage даёт
    в поиске раскрывающиеся вопросы под сниппетом — заметно поднимает кликабельность.
    """
    pairs = re.findall(r"<p><strong>([^<]{10,180}\?)</strong>\s*(.{40,600}?)</p>", body_html, re.S)
    if len(pairs) < 2:
        return None
    clean = lambda s: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s)).strip()
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": clean(q),
             "acceptedAnswer": {"@type": "Answer", "text": clean(a)}}
            for q, a in pairs[:8]
        ],
    }


def strip_unpublished_links(body_html: str, live_slugs: set[str]) -> str:
    """Снимает ссылки на статьи, которые ещё не вышли.

    Статьи ссылаются друг на друга, а выходят по одной в день — до выхода соседа
    ссылка вела бы в 404. Разметку снимаем, текст оставляем; на следующей сборке,
    когда сосед опубликован, ссылка вернётся сама.
    """
    def repl(m: re.Match) -> str:
        href, text = m.group(1), m.group(2)
        slug = href[:-5]
        if href.endswith(".html") and "/" not in href and slug not in live_slugs:
            static = {"index", "blog", "services", "cases", "about", "faq", "contacts",
                      "404", "article", "ai-in-bim", "revit-automation", "dynamo-scripts",
                      "bim-coordination"}
            if slug not in static:
                return text
        return m.group(0)

    return re.sub(r'<a href="([^"]+)">(.*?)</a>', repl, body_html, flags=re.S)


def related(art: dict, arts: list[dict], k: int = 3) -> list[dict]:
    """Соседи по категории, затем просто свежие — для перелинковки."""
    same = [a for a in arts if a["slug"] != art["slug"] and a["category"] == art["category"]]
    rest = [a for a in arts if a["slug"] != art["slug"] and a not in same]
    return (same + rest)[:k]


def page(a: dict, arts: list[dict]) -> str:
    e = html.escape
    url = f"{DOMAIN}/{a['slug']}.html"
    iso = a["publish_at"]
    body = strip_unpublished_links(md_to_html(a["_body"]), {x["slug"] for x in arts})
    kws = a.get("keywords") or []

    jsonld = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": a["title"],
        "description": a["description"],
        "image": f"{DOMAIN}/{a['image']}",
        "datePublished": iso,
        "dateModified": a.get("updated_at", iso),
        "author": {"@type": "Organization", "name": SITE, "url": f"{DOMAIN}/about.html"},
        "publisher": {"@type": "Organization", "name": SITE,
                      "logo": {"@type": "ImageObject", "url": f"{DOMAIN}/logo.png"}},
        "mainEntityOfPage": {"@type": "WebPage", "@id": url},
        "inLanguage": "ru-RU",
    }
    crumbs = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Главная", "item": f"{DOMAIN}/"},
            {"@type": "ListItem", "position": 2, "name": "Блог", "item": f"{DOMAIN}/blog.html"},
            {"@type": "ListItem", "position": 3, "name": a["title"], "item": url},
        ],
    }

    rel = related(a, arts)
    rel_html = "".join(
        f'<li><a href="{r["slug"]}.html">{e(r["title"])}</a></li>' for r in rel
    )
    faq = faq_schema(body)
    faq_ld = (f'\n  <script type="application/ld+json">{json.dumps(faq, ensure_ascii=False)}</script>'
              if faq else "")
    kw_meta = f'\n  <meta name="keywords" content="{e(", ".join(kws))}" />' if kws else ""

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{e(a['title'])} — {SITE}</title>
  <meta name="description" content="{e(a['description'])}" />{kw_meta}
  <meta name="robots" content="index, follow" />
  <link rel="canonical" href="{url}" />
  <meta property="og:type" content="article" />
  <meta property="og:site_name" content="{SITE}" />
  <meta property="og:title" content="{e(a['title'])}" />
  <meta property="og:description" content="{e(a['description'])}" />
  <meta property="og:url" content="{url}" />
  <meta property="og:image" content="{DOMAIN}/og-image.jpg" />
  <meta property="article:published_time" content="{iso}" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{e(a['title'])}" />
  <meta name="twitter:description" content="{e(a['description'])}" />
  <meta name="twitter:image" content="{DOMAIN}/og-image.jpg" />
  <link rel="stylesheet" href="style.css" />
  <link rel="stylesheet" href="article.css" />
  <link rel="stylesheet" href="global.css" />
  <link rel="icon" type="image/png" href="favicon.png" />
  <link rel="apple-touch-icon" href="apple-touch-icon.png" />
  <script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>
  <script type="application/ld+json">{json.dumps(crumbs, ensure_ascii=False)}</script>{faq_ld}
{YM}
</head>
<body>
  <div class="noise"></div>
  {HEADER}
  <main class="article-page section">
    <nav class="breadcrumbs" aria-label="Хлебные крошки">
      <a href="index.html">Главная</a> · <a href="blog.html">Блог</a> · <span>{e(a['category'])}</span>
    </nav>
    <article class="article-full">
    <div class="meta"><span>{e(a['category'])}</span><span>{ru_date(iso)}</span><span>{a['_words']} слов</span></div>
    <h1>{e(a['title'])}</h1>
    <p class="lead">{e(a['description'])}</p>
    <img class="article-cover" src="{e(a['image'])}" alt="{e(a['title'])}" onerror="this.src='bim-model-1.webp'" />
    {body}
    <div class="article-cta">
      <h3>Нужен похожий BIM/AI процесс?</h3>
      <p>Напишите в Telegram или на email — разберём задачу и предложим архитектуру решения.</p>
      <a class="btn primary" href="https://t.me/bim_pulse_ufa" target="_blank" rel="noreferrer">Telegram</a>
      <a class="btn secondary" href="contacts.html">Оставить заявку</a>
    </div>
    <aside class="article-related">
      <h3>Читайте дальше</h3>
      <ul>{rel_html}</ul>
    </aside>
    </article>
  </main>
  {FOOTER}
</body>
</html>
"""


def write_news_js(arts: list[dict]) -> None:
    data = [{
        "slug": a["slug"], "category": a["category"], "date": ru_date(a["publish_at"]),
        "title": a["title"], "excerpt": a["description"], "image": a["image"],
    } for a in arts]
    js = "// Файл генерируется: python3 tools/gen_articles.py. Руками не править.\n"
    js += "window.NEWS = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n"
    (ROOT / "news.js").write_text(js, encoding="utf-8")


def update_blog_html(arts: list[dict]) -> None:
    """Статический список статей в blog.html — чтобы его видел робот без JS."""
    f = ROOT / "blog.html"
    txt = f.read_text(encoding="utf-8")
    cards = "".join(
        f'''
      <article class="blog-card">
        <p class="eyebrow">{html.escape(a["category"])} · {ru_date(a["publish_at"])}</p>
        <h2><a href="{a["slug"]}.html">{html.escape(a["title"])}</a></h2>
        <p>{html.escape(a["description"])}</p>
        <a class="btn" href="{a["slug"]}.html">Читать статью</a>
      </article>'''
        for a in arts
    )
    block = f"      <!-- articles:auto -->{cards}\n      <!-- /articles:auto -->"
    if "<!-- articles:auto -->" in txt:
        txt = re.sub(r"      <!-- articles:auto -->.*?<!-- /articles:auto -->", block, txt, flags=re.S)
    else:
        txt = txt.replace('<div class="news-grid" id="newsGrid"></div>',
                          f'{block}\n    <div class="news-grid" id="newsGrid"></div>')
    f.write_text(txt, encoding="utf-8")


def update_index_html(arts: list[dict], k: int = 3) -> None:
    """Свежие статьи на главной: ссылка с главной ускоряет обход новой страницы."""
    f = ROOT / "index.html"
    txt = f.read_text(encoding="utf-8")
    if "<!-- latest:auto -->" not in txt:
        return
    cards = "".join(f'''
        <a class="news-card" href="{a["slug"]}.html">
          <img src="{a["image"]}" alt="{html.escape(a["title"])}" loading="lazy" onerror="this.src='bim-model-1.webp'">
          <div>
            <div class="meta"><span>{html.escape(a["category"])}</span><span>{ru_date(a["publish_at"])}</span></div>
            <h3>{html.escape(a["title"])}</h3>
            <p>{html.escape(a["description"])}</p>
            <b>Читать →</b>
          </div>
        </a>''' for a in arts[:k])
    block = ('      <!-- latest:auto -->\n'
             '      <p class="eyebrow" style="margin-top:42px">Свежее в блоге</p>\n'
             f'      <div class="news-grid">{cards}\n      </div>\n'
             '      <!-- /latest:auto -->')
    txt = re.sub(r"      <!-- latest:auto -->.*?<!-- /latest:auto -->", block, txt, flags=re.S)
    f.write_text(txt, encoding="utf-8")


def update_sitemap(arts: list[dict]) -> None:
    sm = ROOT / "sitemap.xml"
    txt = sm.read_text(encoding="utf-8")
    block = "  <!-- articles:auto -->\n" + "".join(
        f"  <url>\n    <loc>{DOMAIN}/{a['slug']}.html</loc>\n"
        f"    <lastmod>{a.get('updated_at', a['publish_at'])}</lastmod>\n"
        f"    <priority>0.7</priority>\n  </url>\n" for a in arts
    ) + "  <!-- /articles:auto -->\n"
    txt = re.sub(r"  <!-- articles:auto -->.*?  <!-- /articles:auto -->\n", "", txt, flags=re.S)
    txt = txt.replace("</urlset>", block + "</urlset>")
    sm.write_text(txt, encoding="utf-8")


def main() -> None:
    show_all = "--all" in sys.argv
    today = date.today().isoformat()
    arts = load()
    live = arts if show_all else [a for a in arts if a["publish_at"] <= today]

    # что уже было опубликовано — помним списком, а не по наличию файла на диске:
    # деплой заливает готовые страницы, и «файл существует» перестало значить «опубликовано»
    seen_file = ROOT / "tools" / "published.json"
    seen = set(json.loads(seen_file.read_text(encoding="utf-8"))) if seen_file.exists() else set()

    fresh = []
    for a in live:
        name = f"{a['slug']}.html"
        if a["slug"] not in seen:
            fresh.append(f"{DOMAIN}/{name}")
        (ROOT / name).write_text(page(a, live), encoding="utf-8")
    seen_file.write_text(json.dumps(sorted(seen | {a["slug"] for a in live}),
                                    ensure_ascii=False, indent=1), encoding="utf-8")

    write_news_js(live)
    update_blog_html(live)
    update_index_html(live)
    update_sitemap(live)
    (ROOT / "tools" / "indexnow-new.txt").write_text("\n".join(fresh), encoding="utf-8")

    waiting = len(arts) - len(live)
    print(f"опубликовано страниц: {len(live)} (новых в этот запуск: {len(fresh)}), "
          f"ждут своей даты: {waiting}")
    for a in live[:5]:
        print("  ", a["slug"], a["publish_at"], f"{a['_words']} слов")


if __name__ == "__main__":
    main()
