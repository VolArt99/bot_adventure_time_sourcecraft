# точка входа, инициализация бота, диспетчера, планировщика

# ⚠️ ОБНОВЛЕНО: Улучшенная инициализация и восстановление

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F
from aiogram.exceptions import TelegramNetworkError
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.strategy import FSMStrategy
from config import BOT_TOKEN, GROUP_ID
from database import init_db, sync_topics_from_config
from handlers import common, events, participation, digest, reminders, my_events, roadmap
from utils.scheduler import scheduler, restore_jobs, start_scheduler

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


async def main():
    logger.info("Запуск бота...")

    # Создаём папку для БД
    os.makedirs("data", exist_ok=True)

    # Инициализация БД
    await init_db()
    logger.info("База данных инициализирована")

    await sync_topics_from_config()
    logger.info("Темы из topics_config.py синхронизированы с БД")

    # Инициализация бота
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage(), fsm_strategy=FSMStrategy.GLOBAL_USER)
    dp.message.filter(F.chat.type == "private")
    
    # Регистрация роутеров
    dp.include_router(common.router)
    dp.include_router(events.router)
    dp.include_router(participation.router)
    dp.include_router(digest.router)
    dp.include_router(reminders.router)
    dp.include_router(my_events.router)
    dp.include_router(roadmap.router)
    logger.info("Роутеры зарегистрированы")

    # Регистрируем middleware на основной dispatcher
    from middleware.topic_discoverer import TopicDiscovererMiddleware

    dp.update.middleware(TopicDiscovererMiddleware())

    # Запуск планировщика
    start_scheduler()

    # Восстановление напоминаний
    await restore_jobs(bot)
    logger.info("Напоминания восстановлены")

    # Запуск поллинга с повторными попытками при сетевых сбоях
    logger.info("Запуск поллинга...")
    retry_delay = 5
    max_retry_delay = 60
    while True:
        try:
            await dp.start_polling(bot)
            break
        except TelegramNetworkError as e:
            logger.error(
                f"Ошибка сети при запуске/работе поллинга: {e}. "
                f"Повтор через {retry_delay} сек."
            )
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, max_retry_delay)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
