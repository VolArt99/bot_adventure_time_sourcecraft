from datetime import datetime, timedelta

import pytz

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from bot.config import TIMEZONE, GROUP_ID, ADMIN_IDS
from bot.database import (
    get_user_events,
    get_event,
    get_participants,
    get_main_participants,
    get_topic_name_by_thread_id,
    set_event_responsible,
    add_participant,
    add_driver,
    add_passenger,
)
from bot.keyboards import event_actions, period_keyboard

from bot.texts import format_event_message
from bot.utils.helpers import get_user_mention, build_event_message_link

router = Router()
TZ = pytz.timezone(TIMEZONE)


def _parse_manual_args(message: Message, expected_min: int) -> list[str] | None:
    parts = (message.text or "").split()
    if len(parts) < expected_min:
        return None
    return parts


async def _can_manage_event(event_id: int, user_id: int) -> tuple[bool, dict | None]:
    event = await get_event(event_id)
    if not event:
        return False, None
    if user_id == event["creator_id"] or user_id in ADMIN_IDS:
        return True, event
    return False, event


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
        topic_name = await get_topic_name_by_thread_id(event.get("thread_id"))
        topic_title = topic_name or "Основной чат"
        event_link = build_event_message_link(GROUP_ID, event.get("message_id"))
        link_text = (
            f'<a href="{event_link}">открыть сообщение</a>'
            if event_link
            else "недоступна"
        )

        text_lines.append(
            f"\n<b>{event['title']}</b>\n"
            f"🆔 ID: <code>{event['id']}</code>\n"
            f"🗓 {date_str}\n"
            f"🧵 Тема: {topic_title}\n"
            f"📍 {event.get('location') or 'не указано'}\n"
            f"🔗 Ссылка: {link_text}"
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

    responsible_id = event.get("responsible_id") or event["creator_id"]
    all_users = set(going + waitlist + [event["creator_id"], responsible_id])
    mentions = {uid: await get_user_mention(uid, callback.bot) for uid in all_users}
    organizer_mention = mentions.get(event["creator_id"])
    responsible_mention = mentions.get(responsible_id)

    text = await format_event_message(
        event,
        going,
        waitlist,
        mentions,
        organizer_mention=organizer_mention,
        responsible_mention=responsible_mention,
    )
    await callback.message.answer(
        text,
        reply_markup=event_actions(event_id, event["carpool_enabled"]),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(Command("set_responsible"))
async def cmd_set_responsible(message: Message):
    parts = _parse_manual_args(message, expected_min=3)
    if not parts:
        await message.answer("Использование: /set_responsible <event_id> <user_id>")
        return

    try:
        event_id = int(parts[1])
        responsible_id = int(parts[2])
    except ValueError:
        await message.answer("❌ event_id и user_id должны быть числами.")
        return
    allowed, event = await _can_manage_event(event_id, message.from_user.id)
    if not event:
        await message.answer("❌ Мероприятие не найдено.")
        return
    if not allowed:
        await message.answer("❌ Только создатель или админ может назначать ответственного.")
        return

    await set_event_responsible(event_id, responsible_id)
    await add_participant(event_id, responsible_id, "going")
    from bot.handlers.participation import update_event_message
    await update_event_message(message.bot, event_id, event["thread_id"], event["message_id"])
    await message.answer("✅ Ответственный назначен и добавлен в основной список.")


@router.message(Command("add_participant_manual"))
async def cmd_add_participant_manual(message: Message):
    parts = _parse_manual_args(message, expected_min=3)
    if not parts:
        await message.answer("Использование: /add_participant_manual <event_id> <user_id> [going|waitlist]")
        return

    try:
        event_id = int(parts[1])
        user_id = int(parts[2])
    except ValueError:
        await message.answer("❌ event_id и user_id должны быть числами.")
        return
    status = parts[3].lower() if len(parts) > 3 else "going"
    if status not in {"going", "waitlist"}:
        await message.answer("❌ Статус должен быть going или waitlist.")
        return

    allowed, event = await _can_manage_event(event_id, message.from_user.id)
    if not event:
        await message.answer("❌ Мероприятие не найдено.")
        return
    if not allowed:
        await message.answer("❌ Только создатель или админ может вручную добавлять участников.")
        return

    created = await add_participant(event_id, user_id, status)
    from bot.handlers.participation import update_event_message
    await update_event_message(message.bot, event_id, event["thread_id"], event["message_id"])
    await message.answer("✅ Участник добавлен." if created else "ℹ️ Участник уже был в списке.")


@router.message(Command("set_carpool_manual"))
async def cmd_set_carpool_manual(message: Message):
    parts = _parse_manual_args(message, expected_min=4)
    if not parts:
        await message.answer("Использование: /set_carpool_manual <event_id> <driver_id> <seats>")
        return

    try:
        event_id = int(parts[1])
        driver_id = int(parts[2])
        seats = int(parts[3])
    except ValueError:
        await message.answer("❌ event_id, driver_id и seats должны быть числами.")
        return
    if seats < 1:
        await message.answer("❌ Количество мест должно быть >= 1.")
        return

    allowed, event = await _can_manage_event(event_id, message.from_user.id)
    if not event:
        await message.answer("❌ Мероприятие не найдено.")
        return
    if not allowed:
        await message.answer("❌ Только создатель или админ может настраивать карпулинг.")
        return

    await add_participant(event_id, driver_id, "going")
    ok = await add_driver(event_id, driver_id, seats)
    from bot.handlers.participation import update_event_message
    await update_event_message(message.bot, event_id, event["thread_id"], event["message_id"])
    await message.answer("✅ Водитель сохранён." if ok else "ℹ️ Водитель уже существует.")


@router.message(Command("add_passenger_manual"))
async def cmd_add_passenger_manual(message: Message):
    parts = _parse_manual_args(message, expected_min=4)
    if not parts:
        await message.answer("Использование: /add_passenger_manual <event_id> <passenger_id> <driver_id>")
        return

    try:
        event_id = int(parts[1])
        passenger_id = int(parts[2])
        driver_id = int(parts[3])
    except ValueError:
        await message.answer("❌ event_id, passenger_id и driver_id должны быть числами.")
        return

    allowed, event = await _can_manage_event(event_id, message.from_user.id)
    if not event:
        await message.answer("❌ Мероприятие не найдено.")
        return
    if not allowed:
        await message.answer("❌ Только создатель или админ может настраивать карпулинг.")
        return

    await add_participant(event_id, passenger_id, "going")
    ok = await add_passenger(event_id, passenger_id, driver_id)
    from bot.handlers.participation import update_event_message
    await update_event_message(message.bot, event_id, event["thread_id"], event["message_id"])
    await message.answer("✅ Пассажир добавлен." if ok else "ℹ️ Не удалось добавить пассажира (проверьте места/дубликат).")