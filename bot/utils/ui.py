from __future__ import annotations
import asyncio
from html import escape
from aiogram import Bot


def quote_block(title: str, body_lines: list[str], *, allow_html: bool = False) -> str:
    safe_title = escape(title)
    safe_body = "\n".join((x if allow_html else escape(x)) for x in body_lines if x)
    return f"<blockquote><b>{safe_title}</b>\n{safe_body}</blockquote>"


def ok(text: str) -> str:
    return f"✅ {text}"


def err(text: str) -> str:
    return f"❌ {text}"


async def safe_delete_bot_message(message) -> None:
    """Удаляет сообщение только если оно отправлено ботом."""
    try:
        if message and message.from_user and message.bot and message.from_user.id == message.bot.id:
            await message.delete()
    except Exception:
        pass

    
def info(text: str) -> str:
    return f"ℹ️ {text}"


async def delete_message_later(bot: Bot, chat_id: int, message_id: int, ttl_seconds: int = 20) -> None:
    await asyncio.sleep(max(1, ttl_seconds))
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        return
