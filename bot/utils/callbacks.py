from aiogram.types import CallbackQuery

from bot.utils.ui import safe_delete_bot_message


async def finalize_callback(callback: CallbackQuery, text: str | None = None, *, delete_message: bool = False, show_alert: bool = False) -> None:
    """Единая точка завершения callback: answer + опциональное удаление сообщения бота."""
    await callback.answer(text=text, show_alert=show_alert)
    if delete_message and callback.message:
        await safe_delete_bot_message(callback.message)
