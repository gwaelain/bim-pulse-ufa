#!/usr/bin/env python3
"""Единый источник шапки/футера: подставляет tools/partials/{header,footer}.html
в каждую верхнеуровневую страницу (заменяет существующие <header>/<footer>).
Идемпотентно. Verification-файлы Google/Yandex пропускаются."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HEADER = (ROOT / "tools/partials/header.html").read_text(encoding="utf-8").strip()
FOOTER = (ROOT / "tools/partials/footer.html").read_text(encoding="utf-8").strip()
METRIKA = (ROOT / "tools/partials/metrika.html").read_text(encoding="utf-8").strip()

def process(p: Path) -> bool:
    txt = p.read_text(encoding="utf-8")
    orig = txt
    txt, nh = re.subn(r"<header\b.*?</header>", lambda m: HEADER, txt, count=1, flags=re.S)
    txt, nf = re.subn(r"<footer\b.*?</footer>", lambda m: FOOTER, txt, count=1, flags=re.S)
    txt, nm = re.subn(r"<!-- Yandex\.Metrika counter -->.*?<!-- /Yandex\.Metrika counter -->",
                      lambda m: METRIKA, txt, count=1, flags=re.S)
    if nm == 0:  # аналитики не было — вставляем перед </head>
        txt = txt.replace("</head>", "  " + METRIKA + "\n</head>", 1)
        nm = 1
    if txt != orig:
        p.write_text(txt, encoding="utf-8")
    return nh, nf, nm

def main():
    for p in sorted(ROOT.glob("*.html")):
        if p.name.startswith(("yandex_", "google")):
            continue
        nh, nf, nm = process(p)
        print(f"  {p.name}: header={nh} footer={nf} metrika={nm}")

if __name__ == "__main__":
    main()
