#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Мини-конвертер markdown → HTML без внешних зависимостей.

Поддерживает ровно то, чем пишутся наши статьи: заголовки ##/###, абзацы,
списки (маркированные и нумерованные), таблицы, цитаты, блоки кода,
инлайн `код`, **жирный**, *курсив*, ссылки [текст](url).

Почему свой, а не python-markdown: генератор крутится и на сервере по cron,
где ставить пакеты ради одной функции не хочется.
"""
from __future__ import annotations

import html
import re

__all__ = ["md_to_html", "md_to_text", "frontmatter"]


def frontmatter(raw: str) -> tuple[dict, str]:
    """Разбирает YAML-подобную шапку между --- ... --- (плоские ключи + списки)."""
    m = re.match(r"^﻿?---\s*\n(.*?)\n---\s*\n(.*)$", raw, re.S)
    if not m:
        return {}, raw
    meta: dict = {}
    for line in m.group(1).split("\n"):
        line = line.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        km = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", line)
        if not km:
            continue
        key, val = km.group(1), km.group(2).strip()
        if val.startswith("[") and val.endswith("]"):
            items = [v.strip().strip("\"'") for v in val[1:-1].split(",")]
            meta[key] = [v for v in items if v]
        else:
            meta[key] = val.strip("\"'")
    return meta, m.group(2)


def _inline(s: str) -> str:
    """Инлайн-разметка. Экранируем сначала, потом вставляем теги."""
    s = html.escape(s, quote=False)
    # `код`
    s = re.sub(r"`([^`]+)`", lambda m: f"<code>{m.group(1)}</code>", s)
    # [текст](url)
    s = re.sub(
        r"\[([^\]]+)\]\(([^)\s]+)\)",
        lambda m: f'<a href="{html.escape(m.group(2), quote=True)}">{m.group(1)}</a>',
        s,
    )
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", s)
    return s


def _table(rows: list[str]) -> str:
    def cells(line: str) -> list[str]:
        return [c.strip() for c in line.strip().strip("|").split("|")]

    head = cells(rows[0])
    body = [cells(r) for r in rows[2:]]
    th = "".join(f"<th>{_inline(c)}</th>" for c in head)
    trs = "".join(
        "<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in r) + "</tr>" for r in body
    )
    return f'<div class="table-wrap"><table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>'


def md_to_html(text: str) -> str:
    lines = text.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    i, n = 0, len(lines)

    while i < n:
        line = lines[i]

        if not line.strip():
            i += 1
            continue

        # блок кода
        if line.lstrip().startswith("```"):
            lang = line.strip().strip("`").strip()
            i += 1
            buf = []
            while i < n and not lines[i].lstrip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            cls = f' class="language-{html.escape(lang)}"' if lang else ""
            out.append(f"<pre><code{cls}>{html.escape(chr(10).join(buf))}</code></pre>")
            continue

        # заголовки
        hm = re.match(r"^(#{2,4})\s+(.*)$", line)
        if hm:
            lvl = len(hm.group(1))
            out.append(f"<h{lvl}>{_inline(hm.group(2).strip())}</h{lvl}>")
            i += 1
            continue

        # таблица
        if line.strip().startswith("|") and i + 1 < n and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            buf = []
            while i < n and lines[i].strip().startswith("|"):
                buf.append(lines[i])
                i += 1
            out.append(_table(buf))
            continue

        # цитата
        if line.lstrip().startswith(">"):
            buf = []
            while i < n and lines[i].lstrip().startswith(">"):
                buf.append(lines[i].lstrip()[1:].strip())
                i += 1
            out.append(f"<blockquote><p>{_inline(' '.join(buf))}</p></blockquote>")
            continue

        # списки
        if re.match(r"^\s*[-*+]\s+", line) or re.match(r"^\s*\d+[.)]\s+", line):
            ordered = bool(re.match(r"^\s*\d+[.)]\s+", line))
            items: list[str] = []
            while i < n and (
                re.match(r"^\s*[-*+]\s+", lines[i]) or re.match(r"^\s*\d+[.)]\s+", lines[i])
            ):
                items.append(re.sub(r"^\s*(?:[-*+]|\d+[.)])\s+", "", lines[i]).strip())
                i += 1
                # продолжение пункта с отступом
                while i < n and lines[i].startswith("  ") and lines[i].strip() and not re.match(
                    r"^\s*(?:[-*+]|\d+[.)])\s+", lines[i]
                ):
                    items[-1] += " " + lines[i].strip()
                    i += 1
            tag = "ol" if ordered else "ul"
            lis = "".join(f"<li>{_inline(it)}</li>" for it in items)
            out.append(f"<{tag}>{lis}</{tag}>")
            continue

        # горизонтальная линия
        if re.match(r"^\s*([-*_])\1{2,}\s*$", line):
            out.append("<hr />")
            i += 1
            continue

        # абзац
        buf = [line.strip()]
        i += 1
        while i < n and lines[i].strip() and not re.match(
            r"^\s*(#{2,4}\s|[-*+]\s|\d+[.)]\s|\||>|```)", lines[i]
        ):
            buf.append(lines[i].strip())
            i += 1
        out.append(f"<p>{_inline(' '.join(buf))}</p>")

    return "\n    ".join(out)


def md_to_text(text: str) -> str:
    """Голый текст — для подсчёта слов и excerpt."""
    t = re.sub(r"```.*?```", " ", text, flags=re.S)
    t = re.sub(r"^\s*(#{1,6})\s+", "", t, flags=re.M)
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)
    t = re.sub(r"[*_`>|#-]", " ", t)
    return re.sub(r"\s+", " ", t).strip()
