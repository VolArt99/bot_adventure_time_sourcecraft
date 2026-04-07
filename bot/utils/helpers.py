from aiogram import Bot
from html import escape

async def get_username_by_id(user_id: int, bot: Bot) -> str | None:
    """Возвращает username или имя пользователя."""
    try:
        chat = await bot.get_chat(user_id)
        if chat.username:
            return chat.username
        full_name = " ".join(filter(None, [chat.first_name, getattr(chat, "last_name", None)])).strip()
        return full_name or None
    except Exception:
        return None

async def get_user_mention(user_id: int, bot: Bot) -> str:
    """Возвращает HTML-mention для Telegram."""
    try:
        chat = await bot.get_chat(user_id)
        if chat.username:
            return f"@{escape(chat.username)}"

        full_name = " ".join(
            filter(None, [chat.first_name, getattr(chat, "last_name", None)])
        ).strip() or f"id{user_id}"

        return f'<a href="tg://user?id={user_id}">{escape(full_name)}</a>'
    except Exception:
        return f'<a href="tg://user?id={user_id}">id{user_id}</a>'
