# дайджест, команда /digest

# ⚠️ ОБНОВЛЕНО: Улучшенный дайджест

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from datetime import datetime, timedelta
import pytz
import logging
from config import TIMEZONE, GROUP_ID
from database import get_events_for_digest, get_user_events
from texts import format_digest_text
from utils.helpers import get_username_by_id

logger = logging.getLogger(__name__)
router = Router()
TZ = pytz.timezone(TIMEZONE)

@router.message(Command("digest"))
async def cmd_digest(message: Message):
    """Ручной запуск дайджеста."""
    events = await get_events_for_digest(days=7)
    
    if not events:
        await message.answer("📅 На ближайшую неделю мероприятий не запланировано.")
        return
    
    # Собираем usernames организаторов
    creator_ids = set(e['creator_id'] for e in events)
    usernames = {}
    for cid in creator_ids:
        usernames[cid] = await get_username_by_id(cid, message.bot) or str(cid)
    
    text = format_digest_text(events, usernames)
    await message.answer(text, parse_mode="Markdown")

async def send_digest(bot, chat_id: int, thread_id: int = None):
    """⚠️ НОВОЕ: Автоматическая отправка дайджеста."""
    try:
        events = await get_events_for_digest(days=7)
        if not events:
            return
        
        creator_ids = set(e['creator_id'] for e in events)
        usernames = {}
        for cid in creator_ids:
            usernames[cid] = await get_username_by_id(cid, bot) or str(cid)
        
        text = format_digest_text(events, usernames)
        
        await bot.send_message(
            chat_id=chat_id,
            message_thread_id=thread_id,
            text=text,
            parse_mode="Markdown"
        )
        logger.info("Дайджест отправлен")
    except Exception as e:
        logger.error(f"Ошибка отправки дайджеста: {e}")