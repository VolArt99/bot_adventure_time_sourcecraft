# настройка APScheduler, восстановление задач при старте

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, timedelta
from database import get_active_events, get_event_participants
from config import TIMEZONE
import pytz

scheduler = AsyncIOScheduler(timezone=pytz.timezone(TIMEZONE))

async def schedule_reminders(event):
    """Планирует напоминания для мероприятия."""
    # Список интервалов в секундах до начала
    intervals = [86400, 10800, 7200, 3600, 1800]  # 1д, 3ч, 2ч, 1ч, 30мин
    event_time = datetime.fromisoformat(event['date_time'])
    for interval in intervals:
        remind_time = event_time - timedelta(seconds=interval)
        if remind_time > datetime.now():
            scheduler.add_job(
                send_reminder,
                trigger=DateTrigger(run_date=remind_time),
                args=[event['id'], interval],
                id=f"reminder_{event['id']}_{interval}",
                replace_existing=True
            )

async def send_reminder(event_id, interval):
    """Отправляет напоминание участникам."""
    # Получить список участников (going) и отправить им ЛС
    # ...