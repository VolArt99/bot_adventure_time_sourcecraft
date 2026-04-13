from collections.abc import Callable, Awaitable
from functools import wraps
from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery, TelegramObject

from database import get_or_create_user


class IsRegisteredFilter(BaseFilter):
    """Проверка, что пользователь зарегистрирован (вызвал /start)."""

    async def __call__(self, event: TelegramObject) -> bool:
        user = getattr(event, "from_user", None)
        if not user:
            return False
        
        # Проверяем, что пользователь есть в БД (или создаём)
        user_id = await get_or_create_user(user.id, user.username)
        return bool(user_id)


def registered_user_only(handler: Callable[..., Awaitable]):
    """Декоратор для проверки, что пользователь зарегистрирован."""

    @wraps(handler)
    async def wrapper(event: Message | CallbackQuery, *args, **kwargs):
        user = getattr(event, "from_user", None)
        if not user:
            text = "❌ Не удалось определить пользователя."
            if isinstance(event, CallbackQuery):
                await event.answer(text, show_alert=True)
                return
            await event.answer(text)
            return
        
        # Проверяем, что пользователь есть в БД (или создаём)
        user_id = await get_or_create_user(user.id, user.username)
        if not user_id:
            text = "❌ Пожалуйста, сначала запустите бота командой /start."
            if isinstance(event, CallbackQuery):
                await event.answer(text, show_alert=True)
                return
            await event.answer(text)
            return
        
        return await handler(event, *args, **kwargs)

    return wrapper