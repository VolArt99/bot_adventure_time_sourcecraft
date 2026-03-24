# точка входа, инициализация бота, диспетчера, планировщика

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from database import init_db
from handlers import events, participation, digest, common, reminders
from utils.scheduler import scheduler, restore_jobs

async def main():
    # Настройка логирования
    logging.basicConfig(level=logging.INFO)
    
    # Инициализация БД
    await init_db()
    
    # Бот и диспетчер
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Подключение роутеров
    dp.include_router(common.router)
    dp.include_router(events.router)
    dp.include_router(participation.router)
    dp.include_router(digest.router)
    dp.include_router(reminders.router)
    
    # Запуск планировщика и восстановление задач
    scheduler.start()
    await restore_jobs()
    
    # Запуск поллинга
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())