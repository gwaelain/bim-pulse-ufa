# -*- coding: utf-8 -*-
"""Настройки сервиса заявок и консультанта BIM Pulse. Всё из окружения, секретов в коде нет."""
from __future__ import annotations

import os


def _list(name: str) -> list[str]:
    return [x.strip().lstrip("@") for x in os.environ.get(name, "").split(",") if x.strip()]


BOT_TOKEN = os.environ.get("BIMPULSE_BOT_TOKEN", "")
# кто получает заявки в Telegram: username'ы, которые бот примет как админов по /start
ADMIN_USERNAMES = _list("ADMIN_USERNAMES")

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.yandex.ru")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "465"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
LEAD_EMAIL_TO = os.environ.get("LEAD_EMAIL_TO", SMTP_USER)

DB_PATH = os.environ.get("DB_PATH", "/app/data/bimpulse.db")

# откуда разрешаем запросы к API: сайт и его зеркало, плюс friendlyai — там та же форма
ALLOWED_ORIGINS = _list("ALLOWED_ORIGINS") or ["https://bim-pulse.ru", "https://www.bim-pulse.ru",
                                                "https://friendlyai.ru", "https://www.friendlyai.ru"]

# лимиты — чтобы одна залётная сессия не сожгла бюджет DeepSeek
CHAT_MAX_PER_SESSION_DAY = int(os.environ.get("CHAT_MAX_PER_SESSION_DAY", "40"))
CHAT_MAX_PER_IP_HOUR = int(os.environ.get("CHAT_MAX_PER_IP_HOUR", "120"))
LEAD_MAX_PER_IP_HOUR = int(os.environ.get("LEAD_MAX_PER_IP_HOUR", "5"))
FORM_MIN_SECONDS = float(os.environ.get("FORM_MIN_SECONDS", "3"))  # быстрее человек не заполнит
MAX_MESSAGE_CHARS = 2000
HISTORY_TURNS = 12  # сколько последних реплик отдаём модели
