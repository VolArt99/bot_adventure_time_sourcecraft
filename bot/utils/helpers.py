from aiogram import Bot
from html import escape


def build_event_message_link(chat_id: int, message_id: int | None) -> str | None:
    """Строит ссылку на сообщение в супергруппе/форуме Telegram."""
    if not message_id:
        return None

    chat_str = str(chat_id)
    if chat_str.startswith("-100"):
        chat_part = chat_str[4:]
    elif chat_str.startswith("-"):
        chat_part = chat_str[1:]
    else:
        chat_part = chat_str

    return f"https://t.me/c/{chat_part}/{message_id}"


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
