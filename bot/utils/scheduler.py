# настройка APScheduler, восстановление задач при старте

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from datetime import datetime
import pytz
from config import TIMEZONE

scheduler = AsyncIOScheduler(timezone=pytz.timezone(TIMEZONE))

async def restore_jobs(bot):
    """Восстанавливает напоминания для активных мероприятий при старте."""
    from database import get_active_events
    from handlers.reminders import schedule_reminders_for_event
    events = await get_active_events()
    for event in events:
        await schedule_reminders_for_event(event['id'], bot)