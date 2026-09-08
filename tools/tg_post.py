#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Постинг в Telegram-канал по очереди: один пост за запуск.

Канал из одних ссылок на статьи мёртвый — подписываться там не на что. Поэтому
очередь смешанная: короткие заметки из практики (`content/tg/*.md`) и анонсы
свежих статей. Анонс всегда идёт первым: статья вышла — про неё сразу сказали,
а дальше канал живёт своими заметками.

Очередь лежит в репозитории, значит правится с ПК обычным коммитом.
Состояние (что уже ушло) — на сервере, чтобы пуш сервера не воевал с ПК.

Запуск на сервере по cron 3 раза в день:
    python3 tools/tg_post.py                  # отправить один пост
    python3 tools/tg_post.py --suho           # показать, что ушло бы
    python3 tools/tg_post.py --otmetit-staroe # разметить архив как отправленный

Токен: /opt/drip/tg.env (строка BIMPULSE_BOT_TOKEN=...) либо переменная окружения.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUEUE = ROOT / "content" / "tg"
DOMAIN = "https://bim-pulse.ru"
CHANNEL = "@bim_pulse_ufa"
STATE = Path(os.environ.get("TG_STATE", "/opt/drip/tg-sent.json"))
ENV_FILE = Path("/opt/drip/tg.env")
MIN_GAP_MIN = 90  # не постить чаще, чем раз в полтора часа, даже если cron сдвоился


def token() -> str:
    tok = os.environ.get("BIMPULSE_BOT_TOKEN", "")
    if not tok and ENV_FILE.exists():
        m = re.search(r"BIMPULSE_BOT_TOKEN\s*=\s*(\S+)", ENV_FILE.read_text(encoding="utf-8"))
        tok = m.group(1) if m else ""
    return tok


def frontmatter(text: str) -> tuple[dict, str]:
    m = re.match(r"^﻿?---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).split("\n"):
        km = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", line.strip())
        if km:
            meta[km.group(1)] = km.group(2).strip().strip("\"'")
    return meta, text[m.end():]


def load_state() -> dict:
    return json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}


def save_state(state: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")


def article_meta(slug: str) -> dict | None:
    f = ROOT / "content" / "articles" / f"{slug}.md"
    if not f.exists():
        return None
    meta, _ = frontmatter(f.read_text(encoding="utf-8"))
    return meta


def next_item(state: dict) -> tuple[str, str] | None:
    """Что постим следующим: (ключ для состояния, готовый текст)."""
    sent = set(state.get("sent", []))

    # 1. свежая статья, о которой ещё не говорили
    pub_file = ROOT / "tools" / "published.json"
    if pub_file.exists():
        for slug in json.loads(pub_file.read_text(encoding="utf-8")):
            if slug.startswith("service:") or f"art:{slug}" in sent:
                continue
            meta = article_meta(slug)
            if not meta:
                continue
            text = (f"<b>{meta.get('title', slug)}</b>\n\n"
                    f"{meta.get('description', '')}\n\n"
                    f"{DOMAIN}/{slug}.html")
            return f"art:{slug}", text

    # 2. очередная заметка
    if QUEUE.exists():
        for f in sorted(QUEUE.glob("*.md")):
            key = f"tg:{f.stem}"
            if key in sent:
                continue
            meta, body = frontmatter(f.read_text(encoding="utf-8"))
            return key, body.strip()

    return None


def send(text: str) -> dict:
    tok = token()
    if not tok:
        raise SystemExit("нет токена: положи BIMPULSE_BOT_TOKEN в /opt/drip/tg.env")
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{tok}/sendMessage",
        data=json.dumps({"chat_id": CHANNEL, "text": text, "parse_mode": "HTML",
                         "disable_web_page_preview": False}).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode())


def main() -> int:
    ap = argparse.ArgumentParser(description="Один пост в Telegram-канал")
    ap.add_argument("--suho", action="store_true", help="показать, но не отправлять")
    ap.add_argument("--otmetit-staroe", action="store_true",
                    help="пометить весь текущий архив как отправленный (при первом включении)")
    args = ap.parse_args()

    state = load_state()

    if args.otmetit_staroe:
        sent = set(state.get("sent", []))
        pub = ROOT / "tools" / "published.json"
        if pub.exists():
            sent |= {f"art:{s}" for s in json.loads(pub.read_text(encoding="utf-8"))
                     if not s.startswith("service:")}
        state["sent"] = sorted(sent)
        save_state(state)
        print(f"помечено как отправленное: {len(sent)} записей")
        return 0

    last = state.get("last_at")
    if last and not args.suho:
        gap = (datetime.now(timezone.utc) - datetime.fromisoformat(last)).total_seconds() / 60
        if gap < MIN_GAP_MIN:
            print(f"прошло {gap:.0f} мин с прошлого поста — рано, пропускаем")
            return 0

    item = next_item(state)
    if not item:
        print("очередь пуста — постить нечего")
        return 0

    key, text = item
    print("—" * 60)
    print(text)
    print("—" * 60)

    if args.suho:
        print(f"сухой прогон: ушло бы как {key}")
        return 0

    res = send(text)
    if not res.get("ok"):
        print("ошибка отправки:", res)
        return 1

    state["sent"] = sorted(set(state.get("sent", [])) | {key})
    state["last_at"] = datetime.now(timezone.utc).isoformat()
    save_state(state)
    print(f"отправлено: {key}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
