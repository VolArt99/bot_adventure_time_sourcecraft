from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from filters.admin import admin_only

router = Router(name=__name__)


@router.message(Command("cancel_event"))
@admin_only
async def cmd_cancel_event(message: Message):
    await message.answer(
        "🛑 Сценарий /cancel_event выделен в отдельный модуль. "
        "Сейчас отмена доступна через кнопку «Удалить мероприятие» в карточке события."
    )
