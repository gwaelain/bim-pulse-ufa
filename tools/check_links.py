#!/usr/bin/env python3
"""Офлайн-проверка внутренних ссылок: каждая относительная href/src в *.html
должна указывать на существующий файл. Внешние (http, mailto, tel, //, #, data:)
пропускаются. Код возврата 1 при любой битой ссылке."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP = re.compile(r"^(https?:|mailto:|tel:|//|#|data:|javascript:)", re.I)
REF = re.compile(r'(?:href|src)\s*=\s*"([^"]+)"', re.I)

def main():
    broken = []
    for html in sorted(ROOT.glob("*.html")):
        if html.name.startswith(("yandex_", "google")):
            continue
        text = html.read_text(encoding="utf-8")
        for ref in REF.findall(text):
            if SKIP.match(ref.strip()) or not ref.strip():
                continue
            target = ref.split("?", 1)[0].split("#", 1)[0]
            if not target:
                continue
            if not (ROOT / target).exists():
                broken.append(f"{html.name}: {ref}")
    if broken:
        print("БИТЫЕ внутренние ссылки:")
        for b in broken:
            print("  " + b)
        sys.exit(1)
    print("Внутренние ссылки: OK (битых нет)")

if __name__ == "__main__":
    main()
