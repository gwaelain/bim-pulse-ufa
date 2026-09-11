# -*- coding: utf-8 -*-
"""Уведомления о заявке: всем админам в Telegram и письмом на почту проекта.

Оба канала независимы: упала почта — Telegram дойдёт, и наоборот. Ошибки логируем,
но заявка в базе уже лежит, так что потерять её нельзя.
"""
from __future__ import annotations

import asyncio
import logging
import smtplib
import ssl
from email.header import Header
from email.mime.text import MIMEText
from email.utils import formataddr

import httpx

from . import config, db

log = logging.getLogger("notify")

SOURCE_RU = {
    "contacts": "форма на странице контактов",
    "test": "тест «BIM на 100%»",
    "audit": "форма AI-аудита (friendlyai.ru)",
    "chat": "чат на сайте",
    "telegram": "Telegram-бот",
}


def format_lead(lead_id: int, source: str, site: str | None, name: str, contact: str,
                message: str, extra: dict | None) -> str:
    lines = [f"Заявка №{lead_id} — {SOURCE_RU.get(source, source)}"]
    if site:
        lines.append(f"Сайт: {site}")
    lines.append(f"Имя: {name or '—'}")
    lines.append(f"Контакт: {contact or '—'}")
    if message:
        lines.append(f"\n{message[:1500]}")
    extra = extra or {}
    if extra.get("result"):
        lines.append(f"\nРезультат теста: {extra['result']}")
    if extra.get("gaps"):
        lines.append(f"Что не работает от модели: {extra['gaps']}")
    if extra.get("dialog"):
        lines.append("\nДиалог перед заявкой:")
        for m in extra["dialog"][-8:]:
            who = "Клиент" if m["role"] == "user" else "Консультант"
            lines.append(f"  {who}: {m['content'][:300]}")
    return "\n".join(lines)


async def telegram(text: str) -> None:
    if not config.BOT_TOKEN:
        return
    ids = await db.admin_ids()
    if not ids:
        log.warning("нет админов в Telegram: никто не написал боту /start")
        return
    async with httpx.AsyncClient(timeout=20) as client:
        for chat_id in ids:
            try:
                await client.post(
                    f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendMessage",
                    json={"chat_id": chat_id, "text": text[:4000]})
            except Exception as e:  # noqa: BLE001
                log.error("telegram %s: %s", chat_id, e)


def _send_mail(subject: str, body: str) -> None:
    if not (config.SMTP_USER and config.SMTP_PASSWORD and config.LEAD_EMAIL_TO):
        return
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = formataddr((str(Header("BIM Pulse", "utf-8")), config.SMTP_USER))
    msg["To"] = config.LEAD_EMAIL_TO
    with smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT,
                          context=ssl.create_default_context(), timeout=30) as s:
        s.login(config.SMTP_USER, config.SMTP_PASSWORD)
        s.sendmail(config.SMTP_USER, [config.LEAD_EMAIL_TO], msg.as_string())


async def email(subject: str, body: str) -> None:
    try:
        await asyncio.to_thread(_send_mail, subject, body)
    except Exception as e:  # noqa: BLE001
        log.error("email: %s", e)


async def lead(lead_id: int, source: str, site: str | None, name: str, contact: str,
               message: str, extra: dict | None = None) -> None:
    text = format_lead(lead_id, source, site, name, contact, message, extra)
    await asyncio.gather(
        telegram(text),
        email(f"Заявка №{lead_id}: {SOURCE_RU.get(source, source)}", text),
    )
    await db.mark_notified(lead_id)
