# -*- coding: utf-8 -*-
"""Общая логика диалога для сайта и Telegram: история, ответ модели, перехват контакта."""
from __future__ import annotations

from . import antibot, config, db, llm, notify


async def converse(session_id: str, channel: str, text: str, site: str | None = None,
                   ip: str | None = None, tg_name: str | None = None) -> str:
    text = (text or "").strip()[:config.MAX_MESSAGE_CHARS]
    if not text:
        return "Напишите, пожалуйста, что за задача."

    await db.touch_session(session_id, channel, site)
    if await db.messages_today(session_id) >= config.CHAT_MAX_PER_SESSION_DAY:
        return ("На сегодня лимит сообщений в чате исчерпан. Напишите нам напрямую: "
                "Telegram @bim_pulse_ufa или bimaip@yandex.ru.")

    await db.add_message(session_id, "user", text)

    # контакт в сообщении: превращаем диалог в заявку, но только один раз на сессию
    contact = antibot.find_contact(text)
    if contact and await db.session_lead(session_id) is None:
        hist = await db.history(session_id, limit=20)
        lead_id = await db.add_lead(
            source="telegram" if channel == "telegram" else "chat",
            site=site, name=tg_name or "", contact=contact, message=text,
            extra={"dialog": hist}, ip=ip)
        await db.bind_lead(session_id, lead_id)
        await notify.lead(lead_id, "telegram" if channel == "telegram" else "chat",
                          site, tg_name or "", contact, text, {"dialog": hist})

    hist = await db.history(session_id, limit=config.HISTORY_TURNS * 2)
    try:
        answer = await llm.reply(hist)
    except Exception:  # noqa: BLE001
        answer = ("Сейчас не могу ответить — что-то с подключением к модели. "
                  "Напишите в Telegram @bim_pulse_ufa, там ответим руками.")
    await db.add_message(session_id, "assistant", answer)
    return answer
