#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Пинг IndexNow: сообщаем Яндексу о новых страницах в день их появления.

URL берутся из tools/indexnow-new.txt (пишет gen_articles.py) плюс аргументы командной строки.
Ключ подтверждается файлом в корне сайта: https://bim-pulse.ru/5ce63dcf399ad423cb6f435df02501d4.txt
"""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

HOST = "bim-pulse.ru"
KEY = "5ce63dcf399ad423cb6f435df02501d4"
ENDPOINT = "https://yandex.com/indexnow"
LIST = Path(__file__).resolve().parent / "indexnow-new.txt"


def main() -> int:
    urls = [u.strip() for u in LIST.read_text(encoding="utf-8").splitlines() if u.strip()] if LIST.exists() else []
    urls += [a for a in sys.argv[1:] if a.startswith("http")]
    if not urls:
        print("IndexNow: новых URL нет")
        return 0

    body = json.dumps({
        "host": HOST,
        "key": KEY,
        "keyLocation": f"https://{HOST}/{KEY}.txt",
        "urlList": urls[:100],
    }, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(ENDPOINT, data=body,
                                 headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print(f"IndexNow: HTTP {r.status}, отправлено {len(urls)} URL")
    except Exception as e:
        print(f"IndexNow не дозвонился: {e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
