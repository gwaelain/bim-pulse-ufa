# -*- coding: utf-8 -*-
"""Хранилище: заявки, сессии чата, сообщения, админы. SQLite в volume — как у trest-chat.

Общий Postgres стека не трогаем: объём тут копеечный, а лишняя зависимость от чужой
базы это лишняя точка отказа для формы заявки.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone

import aiosqlite

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    source TEXT NOT NULL,          -- contacts | test | audit | chat | telegram
    site TEXT,                     -- bim-pulse.ru | friendlyai.ru
    name TEXT,
    contact TEXT,
    message TEXT,
    extra TEXT,                    -- json: результат теста, история чата и т.п.
    ip TEXT,
    notified INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS chat_sessions (
    id TEXT PRIMARY KEY,           -- случайный токен из браузера или tg:<user_id>
    channel TEXT NOT NULL,         -- web | telegram
    created_at TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    site TEXT,
    lead_id INTEGER
);
CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    role TEXT NOT NULL,            -- user | assistant
    content TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_msg_session ON chat_messages(session_id, id);
CREATE TABLE IF NOT EXISTS admins (
    chat_id INTEGER PRIMARY KEY,
    username TEXT,
    added_at TEXT NOT NULL
);
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


async def init() -> None:
    os.makedirs(os.path.dirname(config.DB_PATH), exist_ok=True)
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.executescript(SCHEMA)
        await db.commit()


# --- заявки ---

async def add_lead(source: str, site: str | None, name: str, contact: str,
                   message: str, extra: dict | None = None, ip: str | None = None) -> int:
    async with aiosqlite.connect(config.DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO leads (created_at, source, site, name, contact, message, extra, ip) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (now(), source, site, name[:200], contact[:200], message[:4000],
             json.dumps(extra or {}, ensure_ascii=False), ip))
        await db.commit()
        return cur.lastrowid


async def mark_notified(lead_id: int) -> None:
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute("UPDATE leads SET notified=1 WHERE id=?", (lead_id,))
        await db.commit()


async def recent_leads(limit: int = 10) -> list[dict]:
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        rows = await db.execute_fetchall(
            "SELECT * FROM leads ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(r) for r in rows]


# --- чат ---

async def touch_session(session_id: str, channel: str, site: str | None) -> None:
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(
            "INSERT INTO chat_sessions (id, channel, created_at, last_seen, site) VALUES (?,?,?,?,?) "
            "ON CONFLICT(id) DO UPDATE SET last_seen=excluded.last_seen",
            (session_id, channel, now(), now(), site))
        await db.commit()


async def add_message(session_id: str, role: str, content: str) -> None:
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(
            "INSERT INTO chat_messages (session_id, created_at, role, content) VALUES (?,?,?,?)",
            (session_id, now(), role, content))
        await db.commit()


async def history(session_id: str, limit: int = 50) -> list[dict]:
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        rows = await db.execute_fetchall(
            "SELECT role, content, created_at FROM chat_messages WHERE session_id=? "
            "ORDER BY id DESC LIMIT ?", (session_id, limit))
        return [dict(r) for r in reversed(rows)]


async def messages_today(session_id: str) -> int:
    day = now()[:10]
    async with aiosqlite.connect(config.DB_PATH) as db:
        row = await db.execute_fetchall(
            "SELECT COUNT(*) FROM chat_messages WHERE session_id=? AND role='user' "
            "AND substr(created_at,1,10)=?", (session_id, day))
        return row[0][0]


async def session_lead(session_id: str) -> int | None:
    async with aiosqlite.connect(config.DB_PATH) as db:
        row = await db.execute_fetchall(
            "SELECT lead_id FROM chat_sessions WHERE id=?", (session_id,))
        return row[0][0] if row else None


async def bind_lead(session_id: str, lead_id: int) -> None:
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute("UPDATE chat_sessions SET lead_id=? WHERE id=?", (lead_id, session_id))
        await db.commit()


# --- админы ---

async def add_admin(chat_id: int, username: str | None) -> None:
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO admins (chat_id, username, added_at) VALUES (?,?,?)",
            (chat_id, username, now()))
        await db.commit()


async def admin_ids() -> list[int]:
    async with aiosqlite.connect(config.DB_PATH) as db:
        rows = await db.execute_fetchall("SELECT chat_id FROM admins")
        return [r[0] for r in rows]
