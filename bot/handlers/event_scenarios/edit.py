from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from filters.admin import admin_only

router = Router(name=__name__)


@router.message(Command("edit_event"))
@admin_only
async def cmd_edit_event(message: Message):
    await message.answer(
        "✏️ Сценарий /edit_event выделен в отдельный модуль. "
        "Следующий шаг — добавить FSM для редактирования полей выбранного события."
    )
