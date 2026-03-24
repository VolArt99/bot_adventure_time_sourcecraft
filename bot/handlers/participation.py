# обработка кнопок "Пойду", "Отказаться", "В резерв"

from aiogram import Router, F
from aiogram.types import CallbackQuery
from database import get_event, add_participant, remove_participant, move_from_waitlist
from keyboards import event_actions
from texts import format_event_message

router = Router()

@router.callback_query(F.data.startswith("join_"))
async def join_event(callback: CallbackQuery):
    event_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    # Логика добавления в основной список
    # ...
    # После изменения - обновить сообщение
    await callback.message.edit_text(
        text=await format_event_message(event_id),
        reply_markup=event_actions(event_id, carpool_enabled)
    )
    await callback.answer("Вы записаны на мероприятие!")