from datetime import datetime
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.config import OWNER_ID, TIMEZONE
from bot.database import get_user_stats, get_top_participants, find_events
from bot.database import (
    set_random_meeting_opt_in,
    get_random_meeting_opt_in_users,
)
from bot.utils.helpers import get_username_by_id
from bot.utils.pairing import build_random_pairs
from bot.filters.admin import admin_only

import pytz

router = Router()
TZ = pytz.timezone(TIMEZONE)


@router.message(Command("my_stats"))
async def cmd_my_stats(message: Message):
    """Статистика участия пользователя."""
    stats = await get_user_stats(message.from_user.id)
    events_count = stats.get("events_count", 0) or 0
    participations = stats.get("total_participations", 0) or 0

    await message.answer(
        "📊 <b>Ваша статистика</b>\n"
        f"• Уникальных мероприятий: <b>{events_count}</b>\n"
        f"• Подтверждённых участий: <b>{participations}</b>",
        parse_mode="HTML",
    )


@router.message(Command("top"))
async def cmd_top(message: Message):
    """Топ-3 участников за 30 дней."""
    top_users = await get_top_participants(days=30, limit=3)
    if not top_users:
        await message.answer("🏆 За последние 30 дней пока нет данных по посещениям.")
        return

    lines = ["🏆 <b>Топ-3 участников за 30 дней</b>"]
    medals = ["🥇", "🥈", "🥉"]
    for idx, item in enumerate(top_users, start=1):
        username = await get_username_by_id(item["user_id"], message.bot) or f"id{item['user_id']}"
        lines.append(f"{medals[idx-1]} {username} — {item['participations']} участий")

    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("find_events"))
async def cmd_find_events(message: Message):
    """Поиск мероприятий по тексту. Пример: /find_events вело"""
    args = (message.text or "").split(maxsplit=1)
    if len(args) < 2 or not args[1].strip():
        await message.answer(
            "🔎 Использование: <code>/find_events текст_поиска</code>\n"
            "Ищет по названию, месту и категории среди активных событий на месяц.",
            parse_mode="HTML",
        )
        return

    query = args[1].strip()
    events = await find_events(query=query, period="month", limit=20)
    if not events:
        await message.answer(f"📭 По запросу «{query}» ничего не найдено на ближайший месяц.")
        return

    lines = [f"🔎 <b>Найдено: {len(events)}</b>"]
    for event in events:
        dt = datetime.fromisoformat(event["date_time"]).astimezone(TZ)
        lines.append(
            f"\n<b>{event['title']}</b>\n"
            f"🗓 {dt.strftime('%d.%m.%Y %H:%M')}\n"
            f"📍 {event.get('location') or 'не указано'}"
        )

    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("random_optin"))
async def cmd_random_optin(message: Message):
    await set_random_meeting_opt_in(message.from_user.id, True)
    await message.answer("✅ Вы участвуете в рандомных встречах 1:1.")


@router.message(Command("random_optout"))
async def cmd_random_optout(message: Message):
    await set_random_meeting_opt_in(message.from_user.id, False)
    await message.answer("👌 Вы исключены из рандомных встреч 1:1.")


@router.message(Command("random_pairs"))
@admin_only
async def cmd_random_pairs(message: Message):
    users = await get_random_meeting_opt_in_users()
    if len(users) < 2:
        await message.answer("Недостаточно участников с согласием для 1:1.")
        return

    pairs, leftovers = build_random_pairs(users)
    lines = [f"🤝 Сформировано пар: {len(pairs)}"]
    for left_id, right_id in pairs:
        left_name = await get_username_by_id(left_id, message.bot) or f"id{left_id}"
        right_name = await get_username_by_id(right_id, message.bot) or f"id{right_id}"
        lines.append(f"• {left_name} ↔ {right_name}")
        for uid, partner in ((left_id, right_name), (right_id, left_name)):
            try:
                await message.bot.send_message(
                    uid,
                    f"🤝 Ваша случайная встреча 1:1: {partner}. Договоритесь о времени!",
                )
            except Exception:
                pass

    if leftovers:
        lines.append("Ожидают следующего раунда: " + ", ".join(f"id{uid}" for uid in leftovers))

    await message.answer("\n".join(lines))


@router.message(Command("random_optin_count"))
async def cmd_random_optin_count(message: Message):
    if message.from_user.id != OWNER_ID:
        await message.answer("❌ Эта команда доступна только владельцу.")
        return

    users = await get_random_meeting_opt_in_users()
    await message.answer(
        "📊 Согласны на случайные встречи 1:1: "
        f"<b>{len(users)}</b>",
        parse_mode="HTML",
    )