from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
import logging

from config import GROUP_ID
from database import get_events_for_digest, get_topic_name_by_thread_id
from keyboards import period_keyboard
from texts import format_digest_text
from utils.helpers import get_username_by_id, build_event_message_link

logger = logging.getLogger(__name__)
router = Router()


async def enrich_events_with_topic_and_links(events: list[dict]) -> list[dict]:
    enriched_events = []
    for event in events:
        prepared = dict(event)
        prepared["topic_name"] = (
            await get_topic_name_by_thread_id(event.get("thread_id"))
            or "Основной чат"
        )
        prepared["event_link"] = build_event_message_link(GROUP_ID, event.get("message_id"))
        enriched_events.append(prepared)
    return enriched_events


@router.message(Command("digest"))
async def cmd_digest(message: Message):
    """Ручной запуск дайджеста с выбором периода."""
    await message.answer(
        "Выберите период для дайджеста:",
        reply_markup=period_keyboard("digest_period"),
    )


@router.callback_query(F.data.startswith("digest_period_"))
async def digest_with_period(callback: CallbackQuery):
    period = callback.data.removeprefix("digest_period_")
    events = await get_events_for_digest(period=period)

    if not events:
        await callback.message.answer("📅 На выбранный период мероприятий не запланировано.")
        await callback.answer()
        return

    creator_ids = set(e["creator_id"] for e in events)
    usernames = {}
    for cid in creator_ids:
        usernames[cid] = await get_username_by_id(cid, callback.bot) or str(cid)

    enriched_events = await enrich_events_with_topic_and_links(events)
    text = format_digest_text(enriched_events, usernames, period=period)
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()


async def send_digest(bot, chat_id: int, thread_id: int = None):
    """Автоматическая отправка дайджеста."""
    try:
        events = await get_events_for_digest(period="week")
        if not events:
            return

        creator_ids = set(e["creator_id"] for e in events)
        usernames = {}
        for cid in creator_ids:
            usernames[cid] = await get_username_by_id(cid, bot) or str(cid)

        enriched_events = await enrich_events_with_topic_and_links(events)
        text = format_digest_text(enriched_events, usernames, period="week")

        await bot.send_message(
            chat_id=chat_id, message_thread_id=thread_id, text=text, parse_mode="HTML"
        )
        logger.info("Дайджест отправлен")
    except Exception as e:
        logger.error(f"Ошибка отправки дайджеста: {e}")
