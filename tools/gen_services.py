#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сборка страниц услуг из markdown.

Статьи блога отвечают на «как сделать», страницы услуг — на «кто это сделает за меня».
Разбор рынка (14.08.2026) показал: спрос идёт на автоматизацию проверки моделей и
BIM-автоматизацию через API, а коммерческих страниц под эти запросы у нас не было.

Источник — `content/services/<slug>.md`, результат — `<slug>.html` в корне сайта
плюс блок ссылок на services.html и записи в sitemap с повышенным приоритетом.

Запускается из gen_articles.py, отдельно — для отладки:
    python3 tools/gen_services.py
"""
from __future__ import annotations

import html
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from md import frontmatter, md_to_html, md_to_text  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "content" / "services"
DOMAIN = "https://bim-pulse.ru"
SITE = "BIM Pulse Ufa"

HEADER = (ROOT / "tools/partials/header.html").read_text(encoding="utf-8").strip()
FOOTER = (ROOT / "tools/partials/footer.html").read_text(encoding="utf-8").strip()
YM = (ROOT / "tools/partials/metrika.html").read_text(encoding="utf-8").strip()


def load() -> list[dict]:
    items = []
    if not SRC.exists():
        return items
    for f in sorted(SRC.glob("*.md")):
        meta, body = frontmatter(f.read_text(encoding="utf-8"))
        meta.setdefault("slug", f.stem)
        meta.setdefault("publish_at", date.today().isoformat())
        text = md_to_text(body)
        meta.setdefault("title", meta["slug"])
        meta.setdefault("h1", meta["title"])
        meta.setdefault("description", text[:157].rsplit(" ", 1)[0] + "…")
        meta.setdefault("lead", meta["description"])
        meta["_body"] = body
        meta["_words"] = len(text.split())
        items.append(meta)
    return items


def published_slugs() -> set[str]:
    """Слаги статей, которые уже вышли.

    Страницы услуг ссылаются на статьи блога, а те публикуются по расписанию.
    До выхода статьи ссылка вела бы в 404, поэтому её разметку снимаем.
    """
    today = date.today().isoformat()
    live = set()
    arts = ROOT / "content" / "articles"
    if arts.exists():
        for f in arts.glob("*.md"):
            meta, _ = frontmatter(f.read_text(encoding="utf-8"))
            if meta.get("publish_at", today) <= today:
                live.add(meta.get("slug", f.stem))
    return live


def strip_unpublished_links(body_html: str, live: set[str]) -> str:
    static = {"index", "blog", "services", "cases", "about", "faq", "contacts", "404",
              "article", "ai-in-bim", "revit-automation", "dynamo-scripts", "bim-coordination"}

    def repl(m: re.Match) -> str:
        href, text = m.group(1), m.group(2)
        slug = href[:-5]
        if href.endswith(".html") and "/" not in href and slug not in live and slug not in static:
            return text
        return m.group(0)

    return re.sub(r'<a href="([^"]+)">(.*?)</a>', repl, body_html, flags=re.S)


def faq_schema(body_html: str) -> dict | None:
    pairs = re.findall(r"<p><strong>([^<]{10,180}\?)</strong>\s*(.{40,600}?)</p>", body_html, re.S)
    if len(pairs) < 2:
        return None
    clean = lambda s: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s)).strip()
    return {
        "@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": clean(q),
                        "acceptedAnswer": {"@type": "Answer", "text": clean(a)}}
                       for q, a in pairs[:8]],
    }


def page(s: dict, others: list[dict], live: set[str] | None = None) -> str:
    e = html.escape
    url = f"{DOMAIN}/{s['slug']}.html"
    live = live if live is not None else published_slugs()
    live = live | {o["slug"] for o in others}
    body = strip_unpublished_links(md_to_html(s["_body"]), live)
    kws = s.get("keywords") or []
    kw_meta = f'\n  <meta name="keywords" content="{e(", ".join(kws))}" />' if kws else ""

    service_ld = {
        "@context": "https://schema.org",
        "@type": "Service",
        "name": s["h1"],
        "description": s["description"],
        "serviceType": s.get("service_type", s["h1"]),
        "provider": {"@type": "Organization", "name": SITE, "url": f"{DOMAIN}/"},
        "areaServed": {"@type": "Country", "name": "Россия"},
        "url": url,
    }
    crumbs = {
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Главная", "item": f"{DOMAIN}/"},
            {"@type": "ListItem", "position": 2, "name": "Услуги", "item": f"{DOMAIN}/services.html"},
            {"@type": "ListItem", "position": 3, "name": s["h1"], "item": url},
        ],
    }
    faq = faq_schema(body)
    faq_ld = (f'\n  <script type="application/ld+json">{json.dumps(faq, ensure_ascii=False)}</script>'
              if faq else "")

    siblings = "".join(
        f'<li><a href="{o["slug"]}.html">{e(o["h1"])}</a></li>'
        for o in others if o["slug"] != s["slug"])

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{e(s['title'])} — {SITE}</title>
  <meta name="description" content="{e(s['description'])}" />{kw_meta}
  <meta name="robots" content="index, follow" />
  <link rel="canonical" href="{url}" />
  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="{SITE}" />
  <meta property="og:title" content="{e(s['title'])}" />
  <meta property="og:description" content="{e(s['description'])}" />
  <meta property="og:url" content="{url}" />
  <meta property="og:image" content="{DOMAIN}/og-image.jpg" />
  <meta name="twitter:card" content="summary_large_image" />
  <link rel="stylesheet" href="style.css" />
  <link rel="stylesheet" href="article.css" />
  <link rel="stylesheet" href="global.css" />
  <link rel="icon" type="image/png" href="favicon.png" />
  <link rel="apple-touch-icon" href="apple-touch-icon.png" />
  <script type="application/ld+json">{json.dumps(service_ld, ensure_ascii=False)}</script>
  <script type="application/ld+json">{json.dumps(crumbs, ensure_ascii=False)}</script>{faq_ld}
{YM}
</head>
<body>
  <div class="noise"></div>
  {HEADER}
  <main class="article-page section">
    <nav class="breadcrumbs" aria-label="Хлебные крошки">
      <a href="index.html">Главная</a> · <a href="services.html">Услуги</a> · <span>{e(s['h1'])}</span>
    </nav>
    <article class="article-full service-page">
    <p class="eyebrow">Услуга</p>
    <h1>{e(s['h1'])}</h1>
    <p class="lead">{e(s['lead'])}</p>
    {body}
    <div class="article-cta">
      <h3>Обсудим вашу задачу?</h3>
      <p>Опишите, что нужно автоматизировать или проверить — вернёмся с оценкой по объёму и срокам, без «вилки в потолок».</p>
      <a class="btn primary" href="https://t.me/bim_pulse_ufa" target="_blank" rel="noreferrer">Написать в Telegram</a>
      <a class="btn secondary" href="contacts.html">Оставить заявку</a>
    </div>
    <aside class="article-related">
      <h3>Другие услуги</h3>
      <ul>{siblings}</ul>
    </aside>
    </article>
  </main>
  {FOOTER}
</body>
</html>
"""


def update_services_html(items: list[dict]) -> None:
    """Блок ссылок на страницы услуг внутри services.html."""
    f = ROOT / "services.html"
    if not f.exists():
        return
    txt = f.read_text(encoding="utf-8")
    cards = "".join(f'''
      <article class="service-detail">
        <h3><a href="{i["slug"]}.html">{html.escape(i["h1"])}</a></h3>
        <p>{html.escape(i["description"])}</p>
        <a class="text-link" href="{i["slug"]}.html">Подробнее об услуге →</a>
      </article>''' for i in items)
    block = ("      <!-- services:auto -->\n"
             '      <p class="eyebrow" style="margin-top:48px">Подробно по направлениям</p>\n'
             f'      <div class="services-detail-grid">{cards}\n      </div>\n'
             "      <!-- /services:auto -->")
    if "<!-- services:auto -->" in txt:
        txt = re.sub(r"      <!-- services:auto -->.*?<!-- /services:auto -->", block, txt, flags=re.S)
    else:
        txt = txt.replace("</main>", block + "\n</main>", 1)
    f.write_text(txt, encoding="utf-8")


def build() -> list[str]:
    items = load()
    if not items:
        print("страниц услуг нет")
        return []
    for s in items:
        (ROOT / f"{s['slug']}.html").write_text(page(s, items), encoding="utf-8")
    update_services_html(items)
    print(f"собрано страниц услуг: {len(items)}")
    for s in items:
        print("  ", s["slug"], f"{s['_words']} слов")
    return [f"{DOMAIN}/{s['slug']}.html" for s in items]


if __name__ == "__main__":
    build()
