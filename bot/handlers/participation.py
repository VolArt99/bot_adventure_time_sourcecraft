# обработка кнопок "Пойду", "Отказаться", "В резерв"

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from database import get_event, add_participant, remove_participant, get_participants, move_from_waitlist
from keyboards import event_actions
from texts import format_event_message
from utils.helpers import get_username_by_id
from config import GROUP_ID

router = Router()

async def update_event_message(bot: Bot, event_id: int, thread_id: int, message_id: int):
    """Обновляет сообщение мероприятия в группе."""
    event = await get_event(event_id)
    if not event:
        return
    going = await get_participants(event_id, 'going')
    waitlist = await get_participants(event_id, 'waitlist')
    # Собираем имена участников
    all_users = set(going + waitlist)
    usernames = {}
    for uid in all_users:
        usernames[uid] = await get_username_by_id(uid, bot) or str(uid)
    text = format_event_message(event, going, waitlist, usernames)
    await bot.edit_message_text(
        chat_id=GROUP_ID,
        message_id=message_id,
        text=text,
        reply_markup=event_actions(event_id, event['carpool_enabled'])
    )

@router.callback_query(F.data.startswith("join_"))
async def join_event(callback: CallbackQuery):
    event_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    event = await get_event(event_id)
    if not event or event['status'] != 'active':
        await callback.answer("Мероприятие уже завершено или отменено", show_alert=True)
        return
    # Проверяем лимит
    going = await get_participants(event_id, 'going')
    if event['limit'] and len(going) >= event['limit']:
        await callback.answer("Мест нет. Вы можете записаться в резерв", show_alert=True)
        return
    # Проверяем, не состоит ли уже в резерве
    if user_id in await get_participants(event_id, 'waitlist'):
        await callback.answer("Вы уже в резерве. Откажитесь от резерва, чтобы записаться", show_alert=True)
        return
    # Проверяем, не записан ли уже
    if user_id in going:
        await callback.answer("Вы уже записаны", show_alert=True)
        return
    await add_participant(event_id, user_id, 'going')
    await update_event_message(callback.bot, event_id, event['thread_id'], event['message_id'])
    await callback.answer("Вы записаны на мероприятие!")

@router.callback_query(F.data.startswith("decline_"))
async def decline_event(callback: CallbackQuery):
    event_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    event = await get_event(event_id)
    if not event:
        await callback.answer("Мероприятие не найдено", show_alert=True)
        return
    # Удаляем из участников
    await remove_participant(event_id, user_id)
    # Освободилось место? Перемещаем из резерва
    moved_user = await move_from_waitlist(event_id)
    if moved_user:
        # Уведомляем пользователя в ЛС
        try:
            await callback.bot.send_message(moved_user, f"Освободилось место на мероприятии {event['title']}! Вы автоматически добавлены в основной список.")
        except:
            pass
    await update_event_message(callback.bot, event_id, event['thread_id'], event['message_id'])
    await callback.answer("Вы отказались от участия")

@router.callback_query(F.data.startswith("waitlist_"))
async def waitlist_event(callback: CallbackQuery):
    event_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    event = await get_event(event_id)
    if not event or event['status'] != 'active':
        await callback.answer("Мероприятие уже завершено или отменено", show_alert=True)
        return
    # Проверяем, не в основном ли уже
    if user_id in await get_participants(event_id, 'going'):
        await callback.answer("Вы уже в основном списке", show_alert=True)
        return
    # Проверяем, не в резерве ли
    if user_id in await get_participants(event_id, 'waitlist'):
        await callback.answer("Вы уже в резерве", show_alert=True)
        return
    await add_participant(event_id, user_id, 'waitlist')
    await update_event_message(callback.bot, event_id, event['thread_id'], event['message_id'])
    await callback.answer("Вы добавлены в резерв")