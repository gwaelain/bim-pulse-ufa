#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Готовит JPG-копии обложек для RSS-ленты.

На сайте обложки в WebP — он легче и его понимают браузеры. Но Дзен и часть
агрегаторов картинку из `enclosure` в WebP не берут: запись приезжает без
обложки, а в ленте Дзена карточка без картинки почти не собирает показов.
Поэтому рядом держим jpg-копии в `rss-covers/`, на них и ссылается лента.

Файлы лежат в репозитории и едут на сервер вместе с сайтом — при сборке
ничего не конвертируется, Pillow на сервере не нужен.

Запускать руками, когда добавили новую обложку:
    python tools/rss_covers.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "rss-covers"


def main() -> None:
    OUT.mkdir(exist_ok=True)
    made = 0
    for src in sorted(list(ROOT.glob("*.webp")) + list((ROOT / "covers").glob("*.webp"))):
        dst = OUT / f"{src.stem}.jpg"
        if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
            continue
        Image.open(src).convert("RGB").save(dst, "JPEG", quality=86, optimize=True)
        print(f"  {src.name} -> rss-covers/{dst.name} ({dst.stat().st_size // 1024} КБ)")
        made += 1
    print(f"обложек для ленты: {len(list(OUT.glob('*.jpg')))} (пересобрано: {made})")


if __name__ == "__main__":
    main()
