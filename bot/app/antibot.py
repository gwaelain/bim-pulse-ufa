# -*- coding: utf-8 -*-
"""Защита от ботов без капчи. Человеку невидима, автомату мешает.

Четыре слоя, каждый дешёвый:
- honeypot: скрытое поле, которое человек не видит, а робот заполняет;
- время заполнения: форма отдаёт момент открытия, быстрее N секунд человек не успеет;
- Origin/Referer: запросы только с наших сайтов;
- лимиты по IP и по сессии, чтобы и живой человек не мог устроить шквал.
"""
from __future__ import annotations

import re
import time
from collections import defaultdict, deque

from . import config

_hits: dict[str, deque] = defaultdict(deque)


def rate_ok(key: str, limit: int, window_sec: int) -> bool:
    now = time.time()
    q = _hits[key]
    while q and q[0] < now - window_sec:
        q.popleft()
    if len(q) >= limit:
        return False
    q.append(now)
    return True


def origin_ok(origin: str | None, referer: str | None) -> bool:
    src = origin or referer or ""
    return any(src.startswith(o) for o in config.ALLOWED_ORIGINS)


def honeypot_ok(value: str | None) -> bool:
    return not (value or "").strip()


def timing_ok(opened_at_ms: int | float | None) -> bool:
    """opened_at — метка времени, когда форма появилась на экране (мс, от клиента)."""
    if not opened_at_ms:
        return True  # старые формы без метки не режем
    try:
        elapsed = time.time() - float(opened_at_ms) / 1000
    except (TypeError, ValueError):
        return False
    return elapsed >= config.FORM_MIN_SECONDS


CONTACT_RE = re.compile(
    r"([\w.+-]+@[\w-]+\.[\w.-]+)"                   # email
    r"|(@[A-Za-z0-9_]{5,32})"                       # telegram
    r"|(\+?\d[\d\s()-]{9,}\d)",                     # телефон
)


def find_contact(text: str) -> str | None:
    m = CONTACT_RE.search(text or "")
    return m.group(0).strip() if m else None


def looks_like_spam(text: str) -> bool:
    """Грубые признаки: ссылки пачкой, латиница сплошняком в русскоязычной форме."""
    t = text or ""
    if t.count("http") > 2:
        return True
    letters = re.sub(r"[^A-Za-zА-Яа-яЁё]", "", t)
    if len(letters) > 40:
        lat = sum(1 for c in letters if c.isascii())
        if lat / len(letters) > 0.9:
            return True
    return False
