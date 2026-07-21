#!/usr/bin/env python3
"""Гард единого источника: header/footer/Metrika на каждой странице должны
совпадать с партиалами tools/partials/. Ловит ручной дрейф. Код возврата 1
при расхождении. Verification-файлы Google/Yandex пропускаются."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()

PARTS = {
    "header": (r"<header\b.*?</header>", norm((ROOT/"tools/partials/header.html").read_text(encoding="utf-8"))),
    "footer": (r"<footer\b.*?</footer>", norm((ROOT/"tools/partials/footer.html").read_text(encoding="utf-8"))),
    "metrika": (r"<!-- Yandex\.Metrika counter -->.*?<!-- /Yandex\.Metrika counter -->",
                norm((ROOT/"tools/partials/metrika.html").read_text(encoding="utf-8"))),
}

def main():
    drift = []
    for html in sorted(ROOT.glob("*.html")):
        if html.name.startswith(("yandex_", "google")):
            continue
        text = html.read_text(encoding="utf-8")
        for name, (pat, expected) in PARTS.items():
            m = re.search(pat, text, flags=re.S)
            if not m:
                drift.append(f"{html.name}: нет блока {name}")
            elif norm(m.group(0)) != expected:
                drift.append(f"{html.name}: {name} разошёлся с партиалом")
    if drift:
        print("ДРЕЙФ shell-партиалов:")
        for d in drift:
            print("  " + d)
        print("\nЗапусти: python3 tools/apply_shell.py")
        sys.exit(1)
    print("Shell-партиалы: OK (дрейфа нет)")

if __name__ == "__main__":
    main()
