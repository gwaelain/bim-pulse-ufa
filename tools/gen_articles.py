#!/usr/bin/env python3
"""Пререндер статических страниц статей из news.js.

Источник данных — news.js (window.NEWS). Так как это JS, JSON-дамп делается
через JXA: см. tools/build.sh. Здесь на вход подаётся news.json.

Генерирует <slug>.html в корне (относительные пути к ассетам сохраняются),
обновляет блок ссылок статей в sitemap.xml (между маркерами articles:auto).
"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RU_MONTHS = {"января":"01","февраля":"02","марта":"03","апреля":"04","мая":"05",
    "июня":"06","июля":"07","августа":"08","сентября":"09","октября":"10",
    "ноября":"11","декабря":"12"}

def ru_to_iso(date):
    m = re.match(r"(\d{1,2})\s+([а-яё]+)\s+(\d{4})", date, re.I)
    if not m or m.group(2).lower() not in RU_MONTHS:
        return None
    return f"{m.group(3)}-{RU_MONTHS[m.group(2).lower()]}-{int(m.group(1)):02d}"

YM = """  <!-- Yandex.Metrika counter -->
  <script type="text/javascript">
    (function(m,e,t,r,i,k,a){m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};
    m[i].l=1*new Date();k=e.createElement(t),a=e.getElementsByTagName(t)[0];
    k.async=1;k.src=r;a.parentNode.insertBefore(k,a)})(window,document,'script','https://mc.yandex.ru/metrika/tag.js?id=109103460','ym');
    ym(109103460,'init',{webvisor:true,clickmap:true,trackLinks:true,accurateTrackBounce:true});
    ym(109103460,'hit',location.href);
  </script>
  <noscript><div><img src="https://mc.yandex.ru/watch/109103460" style="position:absolute;left:-9999px;" alt="" /></div></noscript>
  <!-- /Yandex.Metrika counter -->"""

def page(a):
    e = html.escape
    slug = a["slug"]; title = a["title"]; desc = a["excerpt"]
    url = f"https://bim-pulse.ru/{slug}.html"
    iso = ru_to_iso(a["date"])
    jsonld = {
        "@context":"https://schema.org","@type":"Article","headline":title,
        "description":desc,"image":f"https://bim-pulse.ru/{a['image']}",
        "author":{"@type":"Organization","name":"BIM Pulse Ufa"},
        "publisher":{"@type":"Organization","name":"BIM Pulse Ufa",
            "logo":{"@type":"ImageObject","url":"https://bim-pulse.ru/logo.png"}},
        "mainEntityOfPage":{"@type":"WebPage","@id":url},
    }
    if iso: jsonld["datePublished"]=iso; jsonld["dateModified"]=iso
    paras = "\n    ".join(f"<p>{e(p)}</p>" for p in a["content"])
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{e(title)} — BIM Pulse Ufa</title>
  <meta name="description" content="{e(desc)}" />
  <meta name="robots" content="index, follow" />
  <link rel="canonical" href="{url}" />
  <meta property="og:type" content="article" />
  <meta property="og:site_name" content="BIM Pulse Ufa" />
  <meta property="og:title" content="{e(title)} — BIM Pulse Ufa" />
  <meta property="og:description" content="{e(desc)}" />
  <meta property="og:url" content="{url}" />
  <meta property="og:image" content="https://bim-pulse.ru/og-image.jpg" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{e(title)} — BIM Pulse Ufa" />
  <meta name="twitter:description" content="{e(desc)}" />
  <meta name="twitter:image" content="https://bim-pulse.ru/og-image.jpg" />
  <link rel="stylesheet" href="style.css" />
  <link rel="icon" type="image/png" href="logo.png" />
  <link rel="apple-touch-icon" href="logo.png" />
  <script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>
{YM}
</head>
<body>
  <div class="noise"></div>
  <header class="site-header">
    <a class="brand" href="index.html"><img src="logo.png" alt="BIM Pulse Ufa" /><span>BIM Pulse Ufa</span></a>
    <nav class="nav"><a href="index.html#services">Услуги</a><a href="index.html#cases">Кейсы</a><a href="index.html#media">Медиа</a><a href="index.html#contacts">Контакты</a></nav>
    <a class="nav-cta" href="https://t.me/bim_pulse_ufa" target="_blank" rel="noreferrer">Telegram</a>
  </header>
  <main class="article-page section">
    <a class="text-link" href="index.html#media">← Назад к медиа</a>
    <article class="article-full">
    <div class="meta"><span>{e(a['category'])}</span><span>{e(a['date'])}</span></div>
    <h1>{e(title)}</h1>
    <p class="lead">{e(desc)}</p>
    <img class="article-cover" src="{e(a['image'])}" alt="{e(title)}" onerror="this.src='bim-model-1.webp'" />
    {paras}
    <div class="article-cta">
      <h3>Нужен похожий BIM/AI процесс?</h3>
      <p>Напишите в Telegram или на email — разберём задачу и предложим архитектуру решения.</p>
      <a class="btn primary" href="https://t.me/bim_pulse_ufa" target="_blank" rel="noreferrer">Telegram</a>
      <a class="btn secondary" href="mailto:im@laingawe.ru">Email</a>
    </div>
    </article>
  </main>
  <footer class="footer"><span>© BIM Pulse Ufa</span><span>im@laingawe.ru</span></footer>
</body>
</html>
"""

def update_sitemap(slugs):
    sm = ROOT / "sitemap.xml"
    txt = sm.read_text(encoding="utf-8")
    block = "  <!-- articles:auto -->\n" + "".join(
        f'  <url>\n    <loc>https://bim-pulse.ru/{s}.html</loc>\n    <priority>0.7</priority>\n  </url>\n'
        for s in slugs) + "  <!-- /articles:auto -->\n"
    txt = re.sub(r"  <!-- articles:auto -->.*?  <!-- /articles:auto -->\n", "", txt, flags=re.S)
    txt = txt.replace("</urlset>", block + "</urlset>")
    sm.write_text(txt, encoding="utf-8")

def main():
    data = json.loads(Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/news.json").read_text(encoding="utf-8"))
    slugs=[]
    for a in data:
        (ROOT / f"{a['slug']}.html").write_text(page(a), encoding="utf-8")
        slugs.append(a["slug"])
    update_sitemap(slugs)
    print(f"сгенерировано страниц: {len(slugs)}")
    for s in slugs: print("  ", f"{s}.html")

if __name__ == "__main__":
    main()
