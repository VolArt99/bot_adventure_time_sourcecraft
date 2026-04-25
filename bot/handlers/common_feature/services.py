from __future__ import annotations

import logging
from aiogram.types import CallbackQuery, Message

from bot.config import GROUP_ID, OWNER_ID
from bot.keyboards import owner_approval_keyboard

logger = logging.getLogger(__name__)


def extract_command(message: Message) -> str | None:
    text = (message.text or "").strip()
    if not text.startswith("/"):
        return None
    return text.split()[0].split("@")[0].lstrip("/").lower()


async def notify_owner_about_request(callback: CallbackQuery) -> None:
    user = callback.from_user
    if OWNER_ID <= 0:
        logger.warning("OWNER_ID не настроен: невозможно отправить заявку владельцу")
        return

    full_name = " ".join(filter(None, [user.first_name, user.last_name])).strip()
    username = f"@{user.username}" if user.username else "—"
    owner_text = (
        "🆕 Запрос на вступление:\n"
        f"• ID: {user.id}\n"
        f"• Имя: {full_name or '—'}\n"
        f"• Username: {username}\n"
        f"• Ссылка: <a href=\"tg://user?id={user.id}\">Перейти в чат</a>"
    )

    await callback.bot.send_message(
        chat_id=OWNER_ID,
        text=owner_text,
        parse_mode="HTML",
        reply_markup=owner_approval_keyboard(user.id),
    )


async def is_user_in_group(message: Message) -> bool:
    try:
        member = await message.bot.get_chat_member(GROUP_ID, message.from_user.id)
    except Exception:
        return False
    return member.status in {"member", "administrator", "creator"}
