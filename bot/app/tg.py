# -*- coding: utf-8 -*-
"""Telegram-бот @bimpulsebot: консультант в личке и доставка заявок админам."""
from __future__ import annotations

import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from . import chat, config, db
from .prompt import WELCOME_TG

log = logging.getLogger("tg")
dp = Dispatcher()


def _is_admin_candidate(m: Message) -> bool:
    u = (m.from_user.username or "").lower()
    return bool(u) and u in [a.lower() for a in config.ADMIN_USERNAMES]


@dp.message(CommandStart())
async def start(m: Message) -> None:
    if _is_admin_candidate(m):
        await db.add_admin(m.chat.id, m.from_user.username)
        await m.answer("Вы подключены как получатель заявок. Сюда будут приходить заявки "
                       "с сайта, из теста и из чата. Команда /leads покажет последние.")
        return
    await m.answer(WELCOME_TG)


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


@dp.message(F.text)
async def talk(m: Message) -> None:
    if m.chat.type != "private":
        return  # в канале и группах молчим: там свой постинг
    if m.chat.id in await db.admin_ids():
        # админу консультант не нужен: он сам команда
        await m.answer("Это ваш служебный диалог: сюда приходят заявки. /leads — последние.")
        return
    name = " ".join(x for x in (m.from_user.first_name, m.from_user.last_name) if x)
    if m.from_user.username:
        name = f"{name} (@{m.from_user.username})".strip()
    answer = await chat.converse(
        session_id=f"tg:{m.from_user.id}", channel="telegram", text=m.text,
        site="telegram", tg_name=name)
    await m.answer(answer)


async def run() -> None:
    if not config.BOT_TOKEN:
        log.warning("BIMPULSE_BOT_TOKEN не задан — бот не запущен")
        return
    bot = Bot(config.BOT_TOKEN)
    # канал @bim_pulse_ufa постит другой скрипт по cron; здесь только личка
    await dp.start_polling(bot, allowed_updates=["message"])
