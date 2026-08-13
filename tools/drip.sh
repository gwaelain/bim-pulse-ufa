#!/usr/bin/env bash
# Капельная публикация статей на сервере (bim-pulse.ru живёт на 5.188.27.237 за Caddy).
#
# Раз в сутки пересобирает сайт из content/articles/*.md: страницы, у которых наступила
# дата publish_at, появляются в корне, попадают в sitemap.xml и в блог, а их адреса
# уходят в IndexNow. Никакого git — сервер собирает то, что уже лежит рядом.
#
# Ставится в cron:
#   5 7 * * * /opt/static/bim-pulse-ufa/tools/drip.sh >> /var/log/bim-pulse-drip.log 2>&1
set -euo pipefail

cd "$(dirname "$0")/.."
echo "=== $(date '+%F %T') drip ==="

python3 tools/gen_articles.py
python3 tools/indexnow.py
