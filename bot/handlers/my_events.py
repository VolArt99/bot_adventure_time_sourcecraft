# ⚠️ НОВОЕ: Обработчик команды /my_events

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from datetime import datetime
import pytz
from config import TIMEZONE, GROUP_ID
from database import get_user_events, get_event, get_participants
from texts import format_event_message
from utils.helpers import get_username_by_id

router = Router()
TZ = pytz.timezone(TIMEZONE)

@router.message(Command("my_events"))
async def cmd_my_events(message: Message):
    """Показывает мероприятия пользователя."""
    user_id = message.from_user.id
    events = await get_user_events(user_id)
    
    if not events:
        await message.answer("📭 У вас нет активных записей на мероприятия.\nИспользуйте /create_event чтобы создать или запишитесь на существующее!")
        return
    
    text = "📅 **Ваши мероприятия:**\n\n"
    for e in events:
        dt = datetime.fromisoformat(e['date_time']).astimezone(TZ)
        date_str = dt.strftime("%d.%m.%Y %H:%M")
        status = "✅ Активно" if e['status'] == 'active' else "⏸ Завершено"
        text += f"**{e['title']}**\n🗓 {date_str}\n📍 {e['location'] or 'не указано'}\n{status}\n\n"
    
    await message.answer(text, parse_mode="Markdown")

@router.callback_query(F.data.startswith("myevent_"))
async def show_my_event(callback: CallbackQuery):
    """Показывает детали конкретного мероприятия."""
    event_id = int(callback.data.split("_")[1])
    event = await get_event(event_id)
    
    if not event:
        await callback.answer("Мероприятие не найдено", show_alert=True)
        return
    
    going = await get_participants(event_id, 'going')
    waitlist = await get_participants(event_id, 'waitlist')
    
    # Собираем usernames
    all_users = set(going + waitlist + [event['creator_id']])
    usernames = {}
    for uid in all_users:
        usernames[uid] = await get_username_by_id(uid, callback.bot) or str(uid)
    
    text = await format_event_message(event, going, waitlist, usernames)
    
    from keyboards import event_actions
    await callback.message.answer(text, reply_markup=event_actions(event_id, event['carpool_enabled']), parse_mode="Markdown")
    await callback.answer()