from datetime import datetime

import pytz

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from config import TIMEZONE
from database import get_user_events, get_event, get_participants, get_main_participants
from keyboards import event_actions

from texts import format_event_message
from utils.helpers import get_user_mention

router = Router()
TZ = pytz.timezone(TIMEZONE)


@router.message(Command("my_events"))
async def cmd_my_events(message: Message):
    """Показывает только активные/будущие мероприятия пользователя."""
    user_id = message.from_user.id
    events = await get_user_events(user_id, status="active")

    now = datetime.now(TZ)
    upcoming = []
    for event in events:
        event_dt = datetime.fromisoformat(event["date_time"]).astimezone(TZ)
        if event_dt >= now:
            upcoming.append(event)

    if not upcoming:
        await message.answer("📭 У вас нет активных мероприятий в будущем.")
        return

    text_lines = ["<b>📅 Ваши активные мероприятия:</b>"]
    for event in upcoming:
        dt = datetime.fromisoformat(event["date_time"]).astimezone(TZ)
        date_str = dt.strftime("%d.%m.%Y %H:%M")
        text_lines.append(
            f"\n<b>{event['title']}</b>\n"
            f"🗓 {date_str}\n"
            f"📍 {event.get('location') or 'не указано'}"
        )

    await message.answer("\n".join(text_lines), parse_mode="HTML")


@router.callback_query(F.data.startswith("myevent_"))
async def show_my_event(callback: CallbackQuery):
    event_id = int(callback.data.split("_")[1])
    event = await get_event(event_id)
    if not event:
        await callback.answer("Мероприятие не найдено", show_alert=True)
        return

    going = await get_main_participants(event_id)
    waitlist = await get_participants(event_id, "waitlist")

    all_users = set(going + waitlist + [event["creator_id"]])
    mentions = {uid: await get_user_mention(uid, callback.bot) for uid in all_users}

    text = await format_event_message(event, going, waitlist, mentions)
    await callback.message.answer(
        text,
        reply_markup=event_actions(event_id, event["carpool_enabled"]),
        parse_mode="HTML",
    )
    await callback.answer()
