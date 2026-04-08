from datetime import datetime

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config import TIMEZONE
from database import get_user_stats, get_top_participants, find_events
from utils.helpers import get_username_by_id
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
