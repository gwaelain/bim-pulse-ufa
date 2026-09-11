# -*- coding: utf-8 -*-
"""Вызов DeepSeek: история диалога → ответ консультанта."""
from __future__ import annotations

import httpx

from . import config
from .prompt import SYSTEM_PROMPT


async def reply(history: list[dict]) -> str:
    """history — список {role, content} без системного сообщения, старые первыми."""
    if not config.DEEPSEEK_API_KEY:
        return ("Консультант временно недоступен. Напишите нам в Telegram @bim_pulse_ufa "
                "или оставьте контакт здесь — ответим в течение рабочего дня.")

    msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in history[-config.HISTORY_TURNS * 2:]:
        msgs.append({"role": m["role"], "content": m["content"][:config.MAX_MESSAGE_CHARS]})

    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            f"{config.DEEPSEEK_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {config.DEEPSEEK_API_KEY}"},
            json={"model": config.DEEPSEEK_MODEL, "messages": msgs,
                  "temperature": 0.6, "max_tokens": 700},
        )
        r.raise_for_status()
        data = r.json()
    text = data["choices"][0]["message"]["content"].strip()
    return text or "Не понял вопрос, переформулируйте, пожалуйста."
