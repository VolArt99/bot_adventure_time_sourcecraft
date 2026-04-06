# точка входа, инициализация бота, диспетчера, планировщика

# ⚠️ ОБНОВЛЕНО: Улучшенная инициализация и восстановление

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN, GROUP_ID
from database import init_db
from handlers import common, events, participation, digest, reminders, my_events
from utils.scheduler import scheduler, restore_jobs, start_scheduler

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Запуск бота...")
    
    # Создаём папку для БД
    os.makedirs("data", exist_ok=True)
    
    # Инициализация БД
    await init_db()
    logger.info("База данных инициализирована")
    
    # Инициализация бота
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Регистрация роутеров
    dp.include_router(common.router)
    dp.include_router(events.router)
    dp.include_router(participation.router)
    dp.include_router(digest.router)
    dp.include_router(reminders.router)
    dp.include_router(my_events.router)  # ⚠️ НОВОЕ
    logger.info("Роутеры зарегистрированы")

    # Регистрируем middleware на основной dispatcher
    from middleware.topic_discoverer import TopicDiscovererMiddleware
    dp.update.middleware(TopicDiscovererMiddleware())
    
    # Запуск планировщика
    start_scheduler()
    
    # Восстановление напоминаний
    await restore_jobs(bot)
    logger.info("Напоминания восстановлены")
    
    # Запуск поллинга
    logger.info("Запуск поллинга...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")