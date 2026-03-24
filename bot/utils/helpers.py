# общие функции (форматирование дат, валидация и т.п.)

from aiogram import Bot

async def get_username_by_id(user_id: int, bot: Bot) -> str:
    """Возвращает username пользователя по ID, если он есть."""
    try:
        chat = await bot.get_chat(user_id)
        return chat.username or chat.first_name
    except:
        return None