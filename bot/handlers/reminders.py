# напоминания (фоновые задачи)

from aiogram import Router, Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
import pytz
from config import TIMEZONE, GROUP_ID
from database import get_active_events, get_participants, get_event
from utils.scheduler import scheduler

router = Router()
TZ = pytz.timezone(TIMEZONE)

async def schedule_reminders_for_event(event_id: int, bot: Bot):
    """Планирует напоминания для мероприятия."""
    event = await get_event(event_id)
    if not event or event['status'] != 'active':
        return
    event_time = datetime.fromisoformat(event['date_time']).astimezone(TZ)
    now = datetime.now(TZ)
    intervals = [86400, 10800, 7200, 3600, 1800]  # 1d, 3h, 2h, 1h, 30min
    for interval in intervals:
        remind_time = event_time - timedelta(seconds=interval)
        if remind_time > now:
            scheduler.add_job(
                send_reminder,
                trigger='date',
                run_date=remind_time,
                args=[event_id, interval, bot],
                id=f"reminder_{event_id}_{interval}",
                replace_existing=True
            )

async def send_reminder(event_id: int, interval: int, bot: Bot):
    """Отправляет напоминание участникам."""
    event = await get_event(event_id)
    if not event or event['status'] != 'active':
        return
    participants = await get_participants(event_id, 'going')
    if not participants:
        return
    dt = datetime.fromisoformat(event['date_time']).astimezone(TZ)
    date_str = dt.strftime("%d.%m.%Y %H:%M")
    text = (
        f"🔔 Напоминание о мероприятии: {event['title']}\n"
        f"🗓 Когда: {date_str}\n"
        f"📍 Где: {event['location'] or 'не указано'}\n"
        f"Ссылка: https://t.me/c/{str(GROUP_ID)[4:]}/{event['message_id']}"
    )
    for uid in participants:
        try:
            await bot.send_message(uid, text)
        except:
            pass
    # Также отправляем в тему
    await bot.send_message(
        chat_id=GROUP_ID,
        message_thread_id=event['thread_id'],
        text=f"🔔 Напоминание: {event['title']} начнётся через {interval // 60} мин"
    )