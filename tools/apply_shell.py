#!/usr/bin/env python3
"""Единый источник шапки/футера: подставляет tools/partials/{header,footer}.html
в каждую верхнеуровневую страницу (заменяет существующие <header>/<footer>).
Идемпотентно. Verification-файлы Google/Yandex пропускаются."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HEADER = (ROOT / "tools/partials/header.html").read_text(encoding="utf-8").strip()
FOOTER = (ROOT / "tools/partials/footer.html").read_text(encoding="utf-8").strip()

def process(p: Path) -> bool:
    txt = p.read_text(encoding="utf-8")
    orig = txt
    txt, nh = re.subn(r"<header\b.*?</header>", lambda m: HEADER, txt, count=1, flags=re.S)
    txt, nf = re.subn(r"<footer\b.*?</footer>", lambda m: FOOTER, txt, count=1, flags=re.S)
    if txt != orig:
        p.write_text(txt, encoding="utf-8")
    return nh, nf

def main():
    for p in sorted(ROOT.glob("*.html")):
        if p.name.startswith(("yandex_", "google")):
            continue
        nh, nf = process(p)
        print(f"  {p.name}: header={nh} footer={nf}")

if __name__ == "__main__":
    main()
