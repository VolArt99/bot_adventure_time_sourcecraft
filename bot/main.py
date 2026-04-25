# точка входа, инициализация бота, диспетчера, планировщика

import json
import base64

import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.exceptions import TelegramNetworkError
from aiogram.fsm.strategy import FSMStrategy

from bot.config import BOT_TOKEN
from bot.database import init_db, sync_topics_from_config
import bot.handlers.common as common
import bot.handlers.events as events
import bot.handlers.participation as participation
import bot.handlers.digest as digest
import bot.handlers.reminders as reminders
import bot.handlers.my_events as my_events
import bot.handlers.roadmap as roadmap
import bot.handlers.subscriptions as subscriptions
import bot.handlers.admin as admin
import bot.handlers.split_bill as split_bill
from bot.utils.scheduler import restore_jobs, start_scheduler
from bot.fsm_storage_ydb import YdbStorage
from bot.init_flags import should_run_schema_init, should_run_schema_init_webhook

from aiogram.types import Update

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
storage = YdbStorage()

dp = Dispatcher(storage=storage, fsm_strategy=FSMStrategy.GLOBAL_USER)
_is_initialized = False
_polling_initialized = False
_init_lock = asyncio.Lock()


def _register_handlers() -> None:
    """Регистрирует роутеры и middleware один раз."""
    dp.message.filter(F.chat.type == "private")

    from bot.middleware.command_access import CommandAccessMiddleware
    dp.message.middleware(CommandAccessMiddleware())

    dp.include_router(common.router)
    dp.include_router(events.router)
    dp.include_router(participation.router)
    dp.include_router(digest.router)
    dp.include_router(reminders.router)
    dp.include_router(my_events.router)
    dp.include_router(roadmap.router)
    dp.include_router(subscriptions.router)
    dp.include_router(split_bill.router)
    dp.include_router(admin.router)

    from bot.middleware.topic_discoverer import TopicDiscovererMiddleware

    dp.update.middleware(TopicDiscovererMiddleware())

async def ensure_initialized(*, for_polling: bool = False) -> None:
    """Ленивая инициализация для polling/webhook режимов."""
    global _is_initialized, _polling_initialized

    if _is_initialized and (not for_polling or _polling_initialized):
        return

    async with _init_lock:
        if _is_initialized and (not for_polling or _polling_initialized):
            return

        if not _is_initialized:
            logger.info("Инициализация бота...")
            run_schema_init = should_run_schema_init() if for_polling else should_run_schema_init_webhook()
            if run_schema_init:
                await init_db()
                logger.info("Схема БД проверена/инициализирована")
            else:
                logger.info("AUTO_INIT_DB disabled: пропускаем init_db() в этом окружении")
            await sync_topics_from_config()
            _register_handlers()
            logger.info("База, темы и роутеры инициализированы")
            _is_initialized = True

        # Планировщик нужен только для long-running polling режима.
        if for_polling and not _polling_initialized:
            start_scheduler()
            await restore_jobs(bot)
            logger.info("Планировщик и напоминания восстановлены")
            _polling_initialized = True

async def handler(event: dict, context):
    body = event.get("body")
    if body is None or body == "":
        # При открытии URL функции в браузере (GET) тело обычно пустое — это не ошибка.
        logger.info("Пустое тело запроса (healthcheck/ручной вызов)")
        return {"statusCode": 200, "body": "OK"}

    if event.get("isBase64Encoded"):
        body = base64.b64decode(body).decode("utf-8")
    elif isinstance(body, bytes):
        body = body.decode("utf-8")

    if not isinstance(body, str):
        logger.warning("Некорректный тип body: %s", type(body).__name__)
        return {"statusCode": 400, "body": "Request body must be a string"}

    try:
        update_data = json.loads(body)
    except json.JSONDecodeError:
        logger.exception("Не удалось распарсить JSON тела запроса")
        return {"statusCode": 400, "body": "Invalid JSON in request body"}

    await ensure_initialized(for_polling=False)

    try:
        await dp.feed_update(
            bot,
            Update.model_validate(update_data),
        )
    except Exception:
        logger.exception("Не удалось обработать update")
        return {"statusCode": 400, "body": "Bad update payload"}

    return {"statusCode": 200, "body": ""}

    
async def main():
    logger.info("Запуск бота...")
    await ensure_initialized(for_polling=True)

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