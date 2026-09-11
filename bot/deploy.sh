#!/usr/bin/env bash
# Деплой сервиса заявок и консультанта на 5.188.27.237.
# Запускать на сервере: bash /opt/drip/bim-pulse-ufa/bot/deploy.sh
# Идемпотентно: повторный запуск ничего не ломает.
set -euo pipefail

REPO=/opt/drip/bim-pulse-ufa
BOT=$REPO/bot
PUBLISH=/opt/drip/bimpulse-publish.sh
CADDY=/opt/stack/Caddyfile

cd "$REPO"
git pull -q || true

# 1. исходники бота не должны попадать в статику сайта
if ! grep -q "exclude 'bot'" "$PUBLISH"; then
  sed -i "s/--exclude '.git' --exclude 'content'/--exclude '.git' --exclude 'bot' --exclude 'content'/" "$PUBLISH"
  echo "publish.sh: bot/ исключён из rsync"
fi
rm -rf /opt/static/bim-pulse-ufa/bot 2>/dev/null || true

# 2. .env должен быть доставлен отдельно (postavit-bimpulse-bot.ps1)
if [ ! -f "$BOT/.env" ]; then
  echo "нет $BOT/.env — сначала залей его скриптом postavit-bimpulse-bot.ps1" >&2
  exit 1
fi

# 3. контейнер
cd "$BOT"
docker compose up -d --build 2>&1 | tail -3

# 4. маршрут в Caddy: /api/* → контейнер. Правим только если ещё нет,
#    и только после validate — Caddy уже роняли неаккуратной правкой.
if ! grep -q "bim-pulse-bot:8000" "$CADDY"; then
  cp "$CADDY" "$CADDY.bak-bimbot-$(date +%Y%m%d-%H%M%S)"
  python3 - "$CADDY" <<'PY'
import re, sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
block = """bim-pulse.ru {
\thandle /api/* {
\t\treverse_proxy bim-pulse-bot:8000
\t}
"""
import re
# якорь с началом строки: первое вхождение подстроки попадало в «www.bim-pulse.ru {»
s2, n = re.subn(r"(?m)^bim-pulse\.ru \{\n", block, s, count=1)
assert n == 1, "блок bim-pulse.ru не найден"
open(p, "w", encoding="utf-8").write(s2)
print("Caddyfile: добавлен handle /api/*")
PY
  if docker exec stack-caddy-1 caddy validate --config /etc/caddy/Caddyfile >/dev/null 2>&1; then
    docker exec stack-caddy-1 caddy reload --config /etc/caddy/Caddyfile 2>/dev/null \
      || docker restart stack-caddy-1 >/dev/null
    echo "Caddy: конфиг валиден, применён"
  else
    echo "Caddy: КОНФИГ НЕ ПРОШЁЛ ПРОВЕРКУ, откатываю" >&2
    cp "$(ls -t $CADDY.bak-bimbot-* | head -1)" "$CADDY"
    exit 1
  fi
fi

sleep 3
echo "--- health ---"
curl -s -m 10 https://bim-pulse.ru/api/health || echo "(health пока не отвечает)"
echo
docker logs --tail 5 bim-pulse-bot 2>&1 | tail -5
