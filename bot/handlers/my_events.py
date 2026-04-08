from datetime import datetime, timedelta

import pytz

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from config import TIMEZONE
from database import get_user_events, get_event, get_participants, get_main_participants
from keyboards import event_actions, period_keyboard

from texts import format_event_message
from utils.helpers import get_user_mention

router = Router()
TZ = pytz.timezone(TIMEZONE)


@router.message(Command("my_events"))
async def cmd_my_events(message: Message):
    """Показывает список мероприятий пользователя с выбором периода."""
    await message.answer(
        "Выберите период для списка ваших мероприятий:",
        reply_markup=period_keyboard("my_events_period"),
    )


@router.callback_query(F.data.startswith("my_events_period_"))
async def my_events_with_period(callback: CallbackQuery):
    period = callback.data.removeprefix("my_events_period_")
    user_id = callback.from_user.id
    events = await get_user_events(user_id, status="active")

    now = datetime.now(TZ)
    period_days = {"week": 7, "month": 30}.get(period)
    future_border = now.replace(microsecond=0)
    future_limit = None if period_days is None else now + timedelta(days=period_days)

    filtered = []
    for event in events:
        dt = datetime.fromisoformat(event["date_time"]).astimezone(TZ)
        if dt < future_border:
            continue
        if future_limit is not None and dt > future_limit:
            continue
        filtered.append(event)

    if not filtered:
        await callback.message.answer("📭 На выбранный период у вас нет активных мероприятий.")
        await callback.answer()
        return

    title_map = {
        "week": "за неделю",
        "month": "за месяц",
        "all": "за всё время",
    }
    text_lines = [f"<b>📅 Ваши активные мероприятия {title_map.get(period, '')}:</b>"]
    for event in filtered:
        dt = datetime.fromisoformat(event["date_time"]).astimezone(TZ)
        date_str = dt.strftime("%d.%m.%Y %H:%M")
        text_lines.append(
            f"\n<b>{event['title']}</b>\n"
            f"🗓 {date_str}\n"
            f"📍 {event.get('location') or 'не указано'}"
        )

    await callback.message.answer("\n".join(text_lines), parse_mode="HTML")
    await callback.answer()


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
