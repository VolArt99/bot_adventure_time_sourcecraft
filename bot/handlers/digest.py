# дайджест, команда /digest

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from datetime import datetime, timedelta
import pytz
from config import TIMEZONE, GROUP_ID
from database import get_active_events
from utils.helpers import get_username_by_id

router = Router()
TZ = pytz.timezone(TIMEZONE)

async def format_digest(bot, events):
    """Формирует текст дайджеста."""
    if not events:
        return "На ближайшую неделю мероприятий не запланировано."
    # Сортируем по дате
    events.sort(key=lambda x: x['date_time'])
    now = datetime.now(TZ)
    week_later = now + timedelta(days=7)
    upcoming = [e for e in events if now <= datetime.fromisoformat(e['date_time']) <= week_later]
    if not upcoming:
        return "На ближайшую неделю мероприятий нет."
    lines = ["📅 Афиша на неделю:\n"]
    for e in upcoming:
        dt = datetime.fromisoformat(e['date_time']).astimezone(TZ)
        date_str = dt.strftime("%d.%m.%Y %H:%M")
        # Получаем имя организатора
        org_name = await get_username_by_id(e['creator_id'], bot) or f"id{e['creator_id']}"
        lines.append(f"🔥 {e['title']}\n🗺 Где: {e['location'] or 'не указано'}\n🗓 Когда: {date_str}\nПо всем вопросам @{org_name}\n")
    return "\n".join(lines)

@router.message(Command("digest"))
async def cmd_digest(message: Message):
    events = await get_active_events()
    digest_text = await format_digest(message.bot, events)
    await message.answer(digest_text, parse_mode="HTML")