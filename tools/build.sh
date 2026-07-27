#!/usr/bin/env bash
# Пререндер страниц статей. Кросс-платформенно: нужен node + python3.
set -euo pipefail
cd "$(dirname "$0")/.."
node tools/dump_news.js
python3 tools/gen_articles.py tools/news.json
