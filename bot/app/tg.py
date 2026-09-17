# -*- coding: utf-8 -*-
"""Telegram-бот @bimpulsebot: консультант в личке, доставка заявок и вопросов админам.

Единая точка входа: кнопки «Написать в Telegram» на сайте ведут сюда с меткой
(`t.me/bimpulsebot?start=contacts`), каждый вопрос человека и ответ консультанта
пересылаются админам, а ответ админа «реплаем» на такое уведомление уходит человеку.
"""
from __future__ import annotations

import logging
import re

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import Message

from . import chat, config, db, notify
from .prompt import WELCOME_TG

log = logging.getLogger("tg")
dp = Dispatcher()

# метка пользователя в уведомлении админам — по ней ищем, кому отвечать реплаем
USER_TAG = re.compile(r"#u(\d+)\b")
SOURCE_RU = {
    "main": "главная", "header": "шапка сайта", "contacts": "контакты", "article": "статья",
    "service": "услуга", "chat": "чат на сайте", "site": "сайт", "test": "тест",
}


def _is_admin_candidate(m: Message) -> bool:
    u = (m.from_user.username or "").lower()
    return bool(u) and u in [a.lower() for a in config.ADMIN_USERNAMES]


def _who(m: Message) -> str:
    name = " ".join(x for x in (m.from_user.first_name, m.from_user.last_name) if x)
    if m.from_user.username:
        name = f"{name} (@{m.from_user.username})".strip()
    return name or f"id{m.from_user.id}"


@dp.message(CommandStart())
async def start(m: Message, command: CommandObject) -> None:
    if _is_admin_candidate(m):
        await db.add_admin(m.chat.id, m.from_user.username)
        await m.answer("Вы подключены как получатель заявок. Сюда приходят заявки с сайта, "
                       "вопросы из этого бота и письма с почты проекта.\n\n"
                       "Ответить человеку — обычным «Ответить» (reply) на его вопрос здесь. "
                       "/leads — последние заявки.")
        return
    src = (command.args or "site").strip()[:32]
    await db.touch_session(f"tg:{m.from_user.id}", "telegram", f"telegram:{src}")
    await m.answer(WELCOME_TG)
    await notify.telegram(f"👋 Новый человек в боте: {_who(m)} #u{m.from_user.id}\n"
                          f"Пришёл: {SOURCE_RU.get(src, src)}")


@dp.message(Command("leads"))
async def leads(m: Message) -> None:
    if m.chat.id not in await db.admin_ids():
        return
    rows = await db.recent_leads(10)
    if not rows:
        await m.answer("Заявок пока нет.")
        return
    out = []
    for r in rows:
        out.append(f"№{r['id']} · {r['created_at'][:16]} · {r['source']} · "
                   f"{r['name'] or '—'} · {r['contact'] or '—'}")
    await m.answer("\n".join(out))


async def _admin_reply(m: Message) -> bool:
    """Админ ответил реплаем на уведомление с меткой #u<id> — доставляем человеку."""
    src = m.reply_to_message
    if not src or not (src.text or src.caption):
        return False
    tag = USER_TAG.search(src.text or src.caption or "")
    if not tag:
        return False
    user_id = int(tag.group(1))
    try:
        await m.bot.send_message(user_id, f"Ответ команды BIM Pulse:\n\n{m.text}")
    except Exception as e:  # noqa: BLE001
        await m.answer(f"Не доставлено: {e}")
        return True
    # чтобы консультант знал, что команда уже ответила, и не спорил с ней
    await db.add_message(f"tg:{user_id}", "assistant", f"[ответ команды] {m.text}")
    await m.answer("Отправлено ✔")
    return True


@dp.message(F.text)
async def talk(m: Message) -> None:
    if m.chat.type != "private":
        return  # в канале и группах молчим: там свой постинг
    if m.chat.id in await db.admin_ids():
        if not await _admin_reply(m):
            await m.answer("Это служебный диалог: сюда приходят заявки и вопросы. Чтобы ответить "
                           "человеку — сделайте «Ответить» на его сообщение. /leads — последние заявки.")
        return
    who = _who(m)
    answer = await chat.converse(
        session_id=f"tg:{m.from_user.id}", channel="telegram", text=m.text,
        site="telegram", tg_name=who)
    await m.answer(answer)
    # копия админам: вопрос целиком, ответ консультанта — коротко
    await notify.telegram(f"💬 Вопрос в боте от {who} #u{m.from_user.id}\n\n{m.text[:1500]}\n\n"
                          f"🤖 Консультант: {answer[:500]}")


async def run() -> None:
    if not config.BOT_TOKEN:
        log.warning("BIMPULSE_BOT_TOKEN не задан — бот не запущен")
        return
    bot = Bot(config.BOT_TOKEN)
    # канал @bim_pulse_ufa постит другой скрипт по cron; здесь только личка
    await dp.start_polling(bot, allowed_updates=["message"])
