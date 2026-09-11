# -*- coding: utf-8 -*-
"""Переносит handle /api/* из блока www.bim-pulse.ru в блок bim-pulse.ru.

Разовая починка: deploy.sh искал первое вхождение «bim-pulse.ru {» и попал в
«www.bim-pulse.ru {». Запуск на сервере: python3 caddy_fix.py /opt/stack/Caddyfile
"""
import re
import sys

p = sys.argv[1]
s = open(p, encoding="utf-8").read()
handle = "\thandle /api/* {\n\t\treverse_proxy bim-pulse-bot:8000\n\t}\n"

# убрать из www-блока, где он не нужен
s = s.replace("www.bim-pulse.ru {\n" + handle, "www.bim-pulse.ru {\n", 1)
# вставить в основной блок — якорь с началом строки, чтобы не зацепить www
s, n = re.subn(r"(?m)^bim-pulse\.ru \{\n", "bim-pulse.ru {\n" + handle, s, count=1)
assert n == 1, "основной блок bim-pulse.ru не найден"
open(p, "w", encoding="utf-8").write(s)
print("Caddyfile: handle /api/* перенесён в bim-pulse.ru")
