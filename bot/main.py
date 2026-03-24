# точка входа, инициализация бота, диспетчера, планировщика

import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from database import init_db
from handlers import common, events, participation, digest, reminders
from utils.scheduler import scheduler, restore_jobs

async def main():
    logging.basicConfig(level=logging.INFO)
    # Создаём папку для БД, если её нет
    os.makedirs("data", exist_ok=True)
    await init_db()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(common.router)
    dp.include_router(events.router)
    dp.include_router(participation.router)
    dp.include_router(digest.router)
    dp.include_router(reminders.router)
    # Запускаем планировщик
    scheduler.start()
    # Восстанавливаем напоминания (требуется bot, передаём)
    await restore_jobs(bot)
    # Запускаем поллинг
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())