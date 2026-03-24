# дайджест, команда /digest

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from database import get_upcoming_events
from texts import format_digest

router = Router()

@router.message(Command("digest"))
async def manual_digest(message: Message):
    # Для ручного формирования
    events = await get_upcoming_events(days=7)
    digest_text = await format_digest(events)
    await message.answer(digest_text, parse_mode="HTML")