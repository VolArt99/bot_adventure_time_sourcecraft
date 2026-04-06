# настройка APScheduler, восстановление задач при старте

# ⚠️ ОБНОВЛЕНО: Восстановление задач при старте бота

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from datetime import datetime, timedelta
import pytz
import logging
from config import TIMEZONE, REMINDER_INTERVALS, GROUP_ID
from database import get_active_events, get_participants, get_event

logger = logging.getLogger(__name__)
TZ = pytz.timezone(TIMEZONE)

# Инициализация планировщика
scheduler = AsyncIOScheduler(
    jobstores={'default': MemoryJobStore()},
    timezone=TZ
)

async def schedule_reminders_for_event(event_id: int, bot):
    """Планирует напоминания для мероприятия."""
    event = await get_event(event_id)
    if not event or event['status'] != 'active':
        return
    
    event_time = datetime.fromisoformat(event['date_time']).astimezone(TZ)
    now = datetime.now(TZ)
    
    for interval in REMINDER_INTERVALS:
        remind_time = event_time - timedelta(seconds=interval)
        if remind_time > now:
            job_id = f"reminder_{event_id}_{interval}"
            scheduler.add_job(
                send_reminder,
                trigger='date',
                run_date=remind_time,
                args=[event_id, interval, bot],
                id=job_id,
                replace_existing=True
            )
            logger.info(f"Запланировано напоминание {job_id} на {remind_time}")

async def send_reminder(event_id: int, interval: int, bot):
    """Отправляет напоминание участникам."""
    try:
        event = await get_event(event_id)
        if not event or event['status'] != 'active':
            return
        
        participants = await get_participants(event_id, 'going')
        if not participants:
            return
        
        minutes_until = interval // 60
        
        from texts import format_reminder_text
        text = format_reminder_text(event, minutes_until)
        
        # Отправка в ЛС
        for uid in participants:
            try:
                await bot.send_message(uid, text, parse_mode="Markdown")
            except Exception as e:
                logger.warning(f"Не удалось отправить ЛС пользователю {uid}: {e}")
        
        # Отправка в тему группы
        if event.get('thread_id'):
            await bot.send_message(
                chat_id=GROUP_ID,
                message_thread_id=event['thread_id'],
                text=f"🔔 Напоминание: **{event['title']}** начнётся через {minutes_until} мин",
                parse_mode="Markdown"
            )
        
        logger.info(f"Напоминание отправлено для мероприятия {event_id}")
    except Exception as e:
        logger.error(f"Ошибка отправки напоминания: {e}")

async def restore_jobs(bot):
    """⚠️ ОБНОВЛЕНО: Восстанавливает напоминания при старте бота."""
    logger.info("Восстановление запланированных напоминаний...")
    events = await get_active_events()
    count = 0
    for event in events:
        await schedule_reminders_for_event(event['id'], bot)
        count += 1
    logger.info(f"Восстановлено {count} мероприятий с напоминаниями")

async def schedule_digest(bot, chat_id: int, thread_id: int = None):
    """Планирует еженедельный дайджест."""
    from handlers.digest import send_digest
    scheduler.add_job(
        send_digest,
        trigger='cron',
        day_of_week=0,  # Понедельник
        hour=10,
        args=[bot, chat_id, thread_id],
        id="weekly_digest",
        replace_existing=True
    )
    logger.info("Запланирован еженедельный дайджест")

# Запуск планировщика
def start_scheduler():
    if not scheduler.running:
        scheduler.start()
        logger.info("Планировщик запущен")