from collections import defaultdict
from datetime import datetime, timezone
import logging
from typing import Awaitable, Callable
from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from bot.config import (
    ADMIN_DAILY_COMMAND_LIMIT,
    ADMIN_IDS,
    MEMBER_ALLOWED_COMMANDS,
    MEMBER_DAILY_COMMAND_LIMIT,
    OUTSIDER_ALLOWED_COMMANDS,
    OUTSIDER_START_DAILY_LIMIT,
    OWNER_ID,
)
from bot.database import is_member_approved
from bot.database import record_command_usage

logger = logging.getLogger(__name__)

class CommandAccessMiddleware(BaseMiddleware):
    """Роли и лимиты по командам в личных сообщениях."""

    def __init__(self) -> None:
        self._daily_usage: dict[tuple[int, str], int] = defaultdict(int)

    @staticmethod
    def _extract_command(message: Message) -> str | None:
        text = message.text or ""
        if not text.startswith("/"):
            return None
        return text.split()[0].split("@")[0].lstrip("/").lower()

    @staticmethod
    def _today_key() -> str:
        return datetime.now(timezone.utc).date().isoformat()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict], Awaitable],
        event: TelegramObject,
        data: dict,
    ):
        if not isinstance(event, Message) or event.chat.type != "private":
            return await handler(event, data)

        user = event.from_user
        if user is None:
            return await handler(event, data)

        command = self._extract_command(event)
        if not command:
            return await handler(event, data)
        state = data.get("state")
        if state is not None and command not in {"create_event"}:
            current_state = await state.get_state()
            if current_state and current_state.startswith("CreateEvent:"):
                await state.clear()
                await event.answer("ℹ️ Предыдущий сценарий создания мероприятия остановлен.")


        user_id = user.id
        is_owner = OWNER_ID > 0 and user_id == OWNER_ID
        is_admin = user_id in ADMIN_IDS
        is_approved_member = await is_member_approved(user_id)

        # Владелец: полный доступ без лимита.
        if is_owner:
            await record_command_usage("owner", command)
            return await handler(event, data)

        # Админ: полный доступ, но с дневным лимитом.
        if is_admin:
            return await self._apply_limit(
                handler,
                event,
                data,
                daily_limit=ADMIN_DAILY_COMMAND_LIMIT,
                role="admin",
                command=command,
                limit_text=(
                    "⚠️ Дневной лимит команд для админа исчерпан. "
                    "Попробуйте снова завтра."
                ),
            )

        # Участник: только разрешённые команды + дневной лимит.
        if is_approved_member:
            if command not in MEMBER_ALLOWED_COMMANDS:
                logger.info(
                    "access_denied user_id=%s command=%s event_id=%s role=member reason=restricted_command",
                    user_id,
                    command,
                    getattr(event, "message_id", None),
                )                
                await event.answer("❌ Эта команда доступна только админу или владельцу.")
                return
            return await self._apply_limit(
                handler,
                event,
                data,
                daily_limit=MEMBER_DAILY_COMMAND_LIMIT,
                role="member",
                command=command,
                limit_text=(
                    "⚠️ Дневной лимит команд исчерпан. "
                    "Попробуйте снова завтра."
                ),
            )

        # Остальные пользователи: ограниченный набор команд с отдельным лимитом.
        if command not in OUTSIDER_ALLOWED_COMMANDS:
            logger.info(
                "access_denied user_id=%s command=%s event_id=%s role=outsider reason=command_not_allowed",
                user_id,
                command,
                getattr(event, "message_id", None),
            )
            await event.answer(
                "❌ До подтверждения доступа вам доступна только команда /start."
            )
            return

        return await self._apply_limit(
            handler,
            event,
            data,
            daily_limit=OUTSIDER_START_DAILY_LIMIT,
            role="outsider",
            command=command,
            limit_text=(
                "⚠️ Дневной лимит команд до одобрения исчерпан. "
                "Попробуйте снова завтра."
            ),
        )

    async def _apply_limit(
        self,
        handler: Callable[[TelegramObject, dict], Awaitable],
        event: Message,
        data: dict,
        *,
        daily_limit: int,
        role: str,
        command: str,
        limit_text: str,
    ):
        today = self._today_key()
        usage_key = (event.from_user.id, today)
        current_usage = self._daily_usage[usage_key]

        if current_usage >= daily_limit:
            await event.answer(limit_text)
            return

        self._daily_usage[usage_key] = current_usage + 1
        await record_command_usage(role, command)
        return await handler(event, data)
