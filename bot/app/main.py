# -*- coding: utf-8 -*-
"""HTTP-часть: приём заявок с форм сайта и чат-консультант для виджета.

Один процесс держит и FastAPI, и Telegram-бота (polling в фоне) — им нужна одна база
и один экземпляр лимитов, а нагрузка тут такая, что делить их незачем.
"""
from __future__ import annotations

import asyncio
import logging
import secrets
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from . import antibot, chat, config, db, notify, tg
from .prompt import WELCOME_WEB

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger("api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init()
    task = asyncio.create_task(tg.run())
    yield
    task.cancel()


app = FastAPI(title="BIM Pulse leads & chat", lifespan=lifespan, docs_url=None, redoc_url=None)
app.add_middleware(CORSMiddleware, allow_origins=config.ALLOWED_ORIGINS,
                   allow_methods=["POST", "GET"], allow_headers=["Content-Type"])


def client_ip(req: Request) -> str:
    return (req.headers.get("x-forwarded-for", "").split(",")[0].strip()
            or (req.client.host if req.client else "?"))


def site_of(req: Request) -> str | None:
    src = req.headers.get("origin") or req.headers.get("referer") or ""
    for host in ("bim-pulse.ru", "friendlyai.ru"):
        if host in src:
            return host
    return None


# --- заявки ---

class LeadIn(BaseModel):
    source: str = Field(default="contacts", max_length=32)
    name: str = Field(default="", max_length=200)
    contact: str = Field(default="", max_length=200)
    message: str = Field(default="", max_length=4000)
    result: str = Field(default="", max_length=300)      # тест: вердикт и процент
    gaps: str = Field(default="", max_length=1000)       # тест: список пробелов
    honey: str = Field(default="", alias="_honey", max_length=200)
    opened_at: float | None = None                       # мс, когда форма показана

    model_config = {"populate_by_name": True}


@app.post("/api/lead")
async def api_lead(body: LeadIn, req: Request):
    ip = client_ip(req)
    # тихие отказы: боту отвечаем «ок», чтобы не подсказывать, что его поймали
    if not antibot.origin_ok(req.headers.get("origin"), req.headers.get("referer")):
        return JSONResponse({"ok": False, "error": "origin"}, status_code=403)
    if not antibot.honeypot_ok(body.honey) or not antibot.timing_ok(body.opened_at):
        log.info("бот отсеян: ip=%s honey=%r opened=%r", ip, body.honey, body.opened_at)
        return {"ok": True}
    if not antibot.rate_ok(f"lead:{ip}", config.LEAD_MAX_PER_IP_HOUR, 3600):
        return {"ok": True}
    if antibot.looks_like_spam(body.message) or not (body.contact.strip() or body.name.strip()):
        return {"ok": True}

    extra = {k: v for k, v in (("result", body.result), ("gaps", body.gaps)) if v}
    site = site_of(req)
    lead_id = await db.add_lead(body.source, site, body.name, body.contact, body.message, extra, ip)
    asyncio.create_task(notify.lead(lead_id, body.source, site, body.name, body.contact,
                                    body.message, extra))
    return {"ok": True, "id": lead_id}


# --- чат ---

class ChatIn(BaseModel):
    session: str = Field(default="", max_length=64)
    text: str = Field(max_length=config.MAX_MESSAGE_CHARS)
    honey: str = Field(default="", alias="_honey", max_length=200)

    model_config = {"populate_by_name": True}


def _valid_session(s: str) -> bool:
    return len(s) == 32 and all(c in "0123456789abcdef" for c in s)


@app.post("/api/chat")
async def api_chat(body: ChatIn, req: Request):
    ip = client_ip(req)
    if not antibot.origin_ok(req.headers.get("origin"), req.headers.get("referer")):
        return JSONResponse({"ok": False, "error": "origin"}, status_code=403)
    if not antibot.honeypot_ok(body.honey):
        return {"ok": True, "session": body.session, "reply": "…"}
    if not antibot.rate_ok(f"chat:{ip}", config.CHAT_MAX_PER_IP_HOUR, 3600):
        return {"ok": True, "session": body.session,
                "reply": "Слишком много запросов. Подождите немного или напишите в @bim_pulse_ufa."}

    session = body.session if _valid_session(body.session) else secrets.token_hex(16)
    answer = await chat.converse(session, "web", body.text, site=site_of(req), ip=ip)
    return {"ok": True, "session": session, "reply": answer}


@app.get("/api/chat/history")
async def api_history(session: str, req: Request):
    if not antibot.origin_ok(req.headers.get("origin"), req.headers.get("referer")):
        return JSONResponse({"ok": False}, status_code=403)
    if not _valid_session(session):
        return {"ok": True, "messages": [], "welcome": WELCOME_WEB}
    msgs = await db.history(session, limit=60)
    return {"ok": True, "messages": msgs, "welcome": WELCOME_WEB}


@app.get("/api/health")
async def health():
    return {"ok": True}
