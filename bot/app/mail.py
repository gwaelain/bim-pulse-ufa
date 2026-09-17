# -*- coding: utf-8 -*-
"""Входящая почта проекта → админам в Telegram и в базу заявок.

Раз в IMAP_POLL_SECONDS читаем непрочитанные письма ящика (тот же логин/пароль
приложения, что и для отправки), пересылаем админам и помечаем прочитанными.
Свои же уведомления «Заявка №…» (они приходят на этот же ящик) пропускаем — иначе петля.
"""
from __future__ import annotations

import asyncio
import email
import email.header
import imaplib
import logging
import re
from email.message import Message

from . import config, db, notify

log = logging.getLogger("mail")


def _decode(value: str | None) -> str:
    if not value:
        return ""
    parts = []
    for chunk, enc in email.header.decode_header(value):
        if isinstance(chunk, bytes):
            parts.append(chunk.decode(enc or "utf-8", "replace"))
        else:
            parts.append(chunk)
    return "".join(parts).strip()


def _body(msg: Message) -> str:
    plain, html = "", ""
    for part in msg.walk() if msg.is_multipart() else [msg]:
        ctype = part.get_content_type()
        if part.get("Content-Disposition", "").startswith("attachment"):
            continue
        if ctype not in ("text/plain", "text/html"):
            continue
        payload = part.get_payload(decode=True) or b""
        text = payload.decode(part.get_content_charset() or "utf-8", "replace")
        if ctype == "text/plain" and not plain:
            plain = text
        elif ctype == "text/html" and not html:
            html = text
    text = plain or re.sub(r"<[^>]+>", " ", re.sub(r"(?is)<(script|style).*?</\1>", "", html))
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def _fetch_unseen() -> list[dict]:
    out = []
    with imaplib.IMAP4_SSL(config.IMAP_HOST, config.IMAP_PORT, timeout=40) as im:
        im.login(config.SMTP_USER, config.SMTP_PASSWORD)
        im.select("INBOX")
        st, data = im.search(None, "UNSEEN")
        ids = data[0].split() if st == "OK" and data and data[0] else []
        for uid in ids[-20:]:  # больше 20 за раз не разгребаем — значит, что-то не то
            st, raw = im.fetch(uid, "(RFC822)")
            if st != "OK" or not raw or not isinstance(raw[0], tuple):
                continue
            msg = email.message_from_bytes(raw[0][1])
            sender = _decode(msg.get("From"))
            subject = _decode(msg.get("Subject"))
            addr = (re.search(r"[\w.+-]+@[\w.-]+", sender) or [None])[0] if sender else None
            out.append({"from": sender, "addr": addr or "", "subject": subject,
                        "text": _body(msg)[:3000], "date": _decode(msg.get("Date"))})
            im.store(uid, "+FLAGS", "\\Seen")
    return out


def _ours(item: dict) -> bool:
    """Наше же уведомление о заявке или письмо от самих себя."""
    if item["addr"].lower() == config.SMTP_USER.lower():
        return True
    return item["subject"].startswith("Заявка №")


async def poll_once() -> int:
    items = await asyncio.to_thread(_fetch_unseen)
    n = 0
    for it in items:
        if _ours(it):
            continue
        name = re.sub(r"<[^>]*>", "", it["from"]).strip(' "') or it["addr"]
        message = f"{it['subject']}\n\n{it['text']}".strip()
        lead_id = await db.add_lead(source="email", site="bimaip@yandex.ru", name=name,
                                    contact=it["addr"], message=message, extra={}, ip=None)
        await notify.telegram(f"📧 Письмо №{lead_id} на почту проекта\n"
                              f"От: {it['from'][:120]}\nТема: {it['subject'][:200] or '—'}\n\n"
                              f"{it['text'][:1500] or '(без текста)'}")
        await db.mark_notified(lead_id)
        n += 1
    return n


async def run() -> None:
    if not (config.SMTP_USER and config.SMTP_PASSWORD and config.IMAP_POLL_SECONDS > 0):
        log.warning("почта не настроена — входящие не читаем")
        return
    while True:
        try:
            n = await poll_once()
            if n:
                log.info("переслано писем: %s", n)
        except Exception as e:  # noqa: BLE001
            log.error("imap: %s", e)
        await asyncio.sleep(config.IMAP_POLL_SECONDS)
