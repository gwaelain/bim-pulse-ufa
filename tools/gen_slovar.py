# -*- coding: utf-8 -*-
"""Словарь BIM-терминов → slovar.html.

Зачем отдельная страница: нейросети и поиск любят короткие определения «X — это…»,
а в Вебмастере уже есть живые запросы ровно такого вида («сводная модель это»,
«файл .cde что такое», «lod bim»). Разметка DefinedTermSet делает страницу
машиночитаемой: ИИ-поиск берёт определение целиком и со ссылкой.

Запуск: python tools/gen_slovar.py (вызывается из gen_articles.py).
Правила: определение — одно-два предложения, без воды; где есть наш разбор — ссылка на статью.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOMAIN = "https://bim-pulse.ru"
SITE = "BIM Pulse Ufa"

# (термин, синонимы для поиска, определение, slug нашей статьи или None)
TERMS: list[tuple[str, str, str, str | None]] = [
    ("BIM", "Building Information Modeling, ТИМ, информационное моделирование",
     "Способ работы, при котором здание описано не чертежами, а моделью с данными: у каждого элемента есть "
     "геометрия и свойства (марка, материал, объём). Из этих данных потом считают смету, график и закуп.", None),
    ("LOD", "уровень проработки, Level of Development",
     "Уровень проработки элемента модели: насколько точна геометрия и насколько заполнены данные. "
     "LOD 200 — обобщённый объект, LOD 350 — с узлами и привязками. Это договорённость в задании, а не свойство файла.",
     "bim-implementation-start"),
    ("LOI", "Level of Information, уровень информации",
     "Уровень информационной наполненности: какие параметры обязаны быть заполнены у элемента. "
     "Часто путают с LOD: можно иметь подробную геометрию и пустые данные — для сметы это бесполезно.", None),
    ("CDE", "СОД, среда общих данных, Common Data Environment",
     "Среда общих данных — единое место, где лежат актуальные версии моделей и документов, с правилами "
     "именования, статусами и историей. Не папка на диске, а процесс: кто, что и когда имеет право менять.",
     "cde-sreda-obshchih-dannyh"),
    ("Сводная модель", "федеративная модель, объединённая модель",
     "Модель, собранная из файлов всех разделов (АР, КР, ОВ, ВК, ЭОМ) для совместной проверки. "
     "Разделы остаются отдельными файлами, в сводной они только связаны — по ней ищут коллизии и считают объёмы.",
     "coordination-federated-model"),
    ("Коллизия", "clash, пересечение, столкновение",
     "Конфликт между элементами разных разделов: пересечение воздуховода с балкой, недостаточный зазор "
     "для монтажа. Делятся на жёсткие (физическое пересечение) и мягкие (нарушение зазора или зоны обслуживания).",
     "navisworks-proverka-kolliziy"),
    ("IFC", "Industry Foundation Classes, обменный формат",
     "Открытый формат обмена моделями между разными программами. Из Revit выгружается с настройками, "
     "и именно в них теряются данные: без нужных наборов свойств смежник получит геометрию без марок и материалов.",
     "ifc-export-iz-revit"),
    ("Dynamo", "Динамо, визуальное программирование",
     "Среда визуального программирования внутри Revit: алгоритм собирается из блоков, без написания кода. "
     "Решает массовые задачи — нумерация, заполнение параметров, выгрузка данных в Excel.",
     "dynamo-pervyy-skript"),
    ("pyRevit", "пайревит",
     "Бесплатное расширение для Revit, которое позволяет добавить свои кнопки на ленту и запускать "
     "Python-скрипты. Ставится за десять минут, компилировать и покупать ничего не нужно.",
     "pyrevit-pervye-knopki"),
    ("Спецификация", "ведомость, schedule, таблица",
     "Таблица в Revit, которая собирает данные элементов модели по заданным правилам. "
     "Считается автоматически и обновляется вместе с моделью — в отличие от таблицы, набранной руками.",
     "revit-specifikacii-v-excel"),
    ("Общие параметры", "ФОП, файл общих параметров, shared parameters",
     "Параметры, которые живут в отдельном файле и одинаково опознаются во всех проектах и семействах. "
     "У каждого — свой GUID: два файла с одинаковыми именами параметров дают пустые столбцы в сводной модели.",
     "revit-avtozapolnenie-parametrov"),
    ("Navisworks", "Навис, Невис",
     "Программа Autodesk для сборки сводной модели и поиска коллизий. Читает форматы разных САПР, "
     "работает с тяжёлыми моделями и даёт отчёты, по которым ведут согласование между разделами.",
     "navisworks-proverka-kolliziy"),
    ("Матрица коллизий", "матрица проверок",
     "Таблица «кто с кем проверяется»: какие разделы и системы сопоставляются между собой и с каким допуском. "
     "Без неё проверка «всё против всего» выдаёт тысячи строк, которые никто не читает.",
     "navisworks-matrica-kolliziy"),
    ("Точка обзора", "viewpoint, точка зрения",
     "Сохранённое положение камеры в Navisworks вместе с настройками отображения. "
     "Используется, чтобы показать коллизию смежнику — но выделение элементов в ней сохраняется не всегда.",
     "navisworks-tochki-obzora"),
    ("EIR", "информационные требования заказчика, Exchange Information Requirements",
     "Требования заказчика к модели: что моделируем, с какой детализацией, какие параметры заполняем "
     "и в каком виде сдаём. Документ, по которому потом принимают работу.", None),
    ("BEP", "план реализации BIM, BIM Execution Plan",
     "Ответ исполнителя на EIR: как именно будет организована работа — структура файлов, "
     "регламент координации, сроки выдач, кто за что отвечает.", "reglament-bim-koordinacii"),
    ("4D", "календарное планирование по модели",
     "Связка модели с календарным графиком: каждому элементу сопоставлен срок работ, и строительство "
     "можно просмотреть во времени. Расхождения графика и модели становятся видны до выхода на площадку.",
     "bim-dashboard"),
    ("Классификатор", "кодификатор, классификация элементов",
     "Система кодов, по которой элементы модели сопоставляются со сметными расценками и номенклатурой "
     "снабжения. Без единого классификатора данные модели не доезжают до сметы без ручного переноса.",
     "postgresql-bim-data"),
    ("NWC и NWD", "форматы Navisworks",
     "NWC — промежуточный файл выгрузки из Revit или другой САПР, NWD — собранная сводная модель "
     "одним файлом со всей геометрией. NWF хранит только ссылки на исходники и настройки.",
     "navisworks-proverka-kolliziy"),
    ("Revit API", "программный интерфейс Revit",
     "Программный интерфейс Revit: позволяет писать плагины на C# или Python, которые делают с моделью то, "
     "чего нет в стандартных командах — свои проверки, выгрузки, массовые операции.",
     "razrabotka-dynamo-i-plaginov"),
]


def page() -> str:
    e = html.escape
    items = []
    for term, syn, definition, slug in TERMS:
        link = (f'<p class="slovar-more"><a href="{slug}.html">Разбор из практики →</a></p>' if slug else "")
        syn_html = f'<p class="slovar-syn">Также говорят: {e(syn)}</p>' if syn else ""
        items.append(
            f'      <article class="slovar-item" id="{e(term.lower().replace(" ", "-"))}">\n'
            f'        <h2>{e(term)}</h2>\n'
            f'        <p>{e(definition)}</p>\n'
            f'        {syn_html}\n        {link}\n      </article>')

    ld_terms = [{"@type": "DefinedTerm", "name": term, "description": definition,
                 "inDefinedTermSet": f"{DOMAIN}/slovar.html",
                 "url": f"{DOMAIN}/slovar.html#{term.lower().replace(' ', '-')}"}
                for term, _syn, definition, _slug in TERMS]
    ld_set = {"@context": "https://schema.org", "@type": "DefinedTermSet",
              "name": "Словарь BIM-терминов", "url": f"{DOMAIN}/slovar.html",
              "description": "Короткие определения терминов BIM: LOD, CDE, IFC, коллизии, сводная модель, "
                             "общие параметры, матрица коллизий и другие.",
              "inLanguage": "ru-RU", "publisher": {"@id": f"{DOMAIN}/#org"},
              "hasDefinedTerm": ld_terms}
    crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Главная", "item": f"{DOMAIN}/"},
        {"@type": "ListItem", "position": 2, "name": "Словарь BIM-терминов", "item": f"{DOMAIN}/slovar.html"}]}

    head = (ROOT / "tools" / "partials" / "header.html").read_text(encoding="utf-8")
    foot = (ROOT / "tools" / "partials" / "footer.html").read_text(encoding="utf-8")
    ym = (ROOT / "tools" / "partials" / "metrika.html").read_text(encoding="utf-8")
    nl = "\n"
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">

  <title>Словарь BIM-терминов: LOD, CDE, IFC, коллизии простыми словами</title>
  <meta name="description" content="Что такое LOD, CDE, IFC, сводная модель, коллизия и общие параметры — короткие определения без воды, со ссылками на разборы из практики.">
  <meta name="robots" content="index, follow">

  <link rel="canonical" href="{DOMAIN}/slovar.html">
  <link rel="icon" type="image/png" href="favicon.png">
  <link rel="apple-touch-icon" href="apple-touch-icon.png">

  <meta property="og:type" content="website">
  <meta property="og:title" content="Словарь BIM-терминов простыми словами">
  <meta property="og:description" content="LOD, CDE, IFC, сводная модель, коллизия, общие параметры — короткие определения и ссылки на разборы.">
  <meta property="og:url" content="{DOMAIN}/slovar.html">
  <meta property="og:image" content="{DOMAIN}/og-image.jpg">
  <meta name="twitter:card" content="summary_large_image">

  <link rel="stylesheet" href="style.css">
  <link rel="stylesheet" href="global.css">

  <script type="application/ld+json">
  {json.dumps(ld_set, ensure_ascii=False)}
  </script>
  <script type="application/ld+json">
  {json.dumps(crumbs, ensure_ascii=False)}
  </script>
  <style>
    .slovar-list {{ display: grid; gap: 16px; }}
    .slovar-item {{ padding: 24px 26px; border: 1px solid var(--line); border-radius: 20px; background: var(--panel); }}
    .slovar-item h2 {{ margin: 0 0 10px; font-size: 21px; }}
    .slovar-item p {{ margin: 0 0 8px; color: var(--soft); line-height: 1.55; }}
    .slovar-syn {{ font-size: 14px; color: var(--muted); }}
    .slovar-more a {{ color: var(--accent); font-size: 15px; }}
    .slovar-abc {{ display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 28px; }}
    .slovar-abc a {{ padding: 7px 14px; border: 1px solid var(--line); border-radius: 999px; font-size: 14px; color: var(--soft); }}
    .slovar-abc a:hover {{ border-color: var(--accent); color: var(--accent); }}
  </style>
{ym}
</head>

<body>
  <div class="noise"></div>

{head}
  <main class="page">
    <section class="section hero-section">
      <p class="eyebrow">Справочник</p>
      <h1>Словарь BIM-терминов</h1>
      <p class="lead">
        Короткие определения без воды: что означает термин и чем он важен на практике.
        Где у нас есть подробный разбор — стоит ссылка.
      </p>
    </section>

    <section class="section">
      <nav class="slovar-abc" aria-label="Термины">
{nl.join(f'        <a href="#{t.lower().replace(" ", "-")}">{t}</a>' for t, _s, _d, _sl in TERMS)}
      </nav>
      <div class="slovar-list">
{nl.join(items)}
      </div>
    </section>

    <section class="section">
      <div class="article-cta">
        <h3>Не нашли термин или спорите о трактовке?</h3>
        <p>Напишите — ответим по существу и добавим определение в словарь.</p>
        <a class="btn primary" href="https://t.me/bimpulsebot?start=slovar" target="_blank" rel="noopener" onclick="ymGoal('telegram_click')">Задать вопрос</a>
        <a class="btn secondary" href="services.html">Посмотреть услуги</a>
      </div>
    </section>
  </main>

{foot}
</body>
</html>
"""


def main() -> None:
    (ROOT / "slovar.html").write_text(page(), encoding="utf-8")
    print(f"slovar.html: {len(TERMS)} терминов")


if __name__ == "__main__":
    main()
