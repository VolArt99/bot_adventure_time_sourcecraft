from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
import logging
import aiogram

from config import GROUP_ID
from database import get_or_create_user
from filters.admin import admin_only

logger = logging.getLogger(__name__)
router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    await get_or_create_user(user_id, username)
    await message.answer("Привет! Я бот для управления мероприятиями в группе.")


@router.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        "ℹ️ <b>Все команды работают только в личных сообщениях с ботом.</b>\n\n"
        "<b>Основные команды:</b>\n"
        "/start — регистрация и запуск бота\n"
        "/help — список команд и возможностей\n"
        "/create_event — создать мероприятие (для организаторов)\n"
        "/my_events — мои мероприятия (неделя/месяц/всё время)\n"
        "/digest — дайджест мероприятий (неделя/месяц/всё время)\n"
        "/subscriptions — подписки на категории\n"
        "/my_digest — персональный дайджест по подпискам\n"
        "/my_stats — ваша статистика посещений\n"
        "/top — топ-3 участников за 30 дней\n"
        "/find_events — поиск активных событий по тексту\n\n"
        "<b>Админ/сервис:</b>\n"
        "/debug_info — единая диагностика (бот, группа, права, темы)\n"
        "/health — быстрая проверка работоспособности\n"
        "/list_topics — список обнаруженных тем\n"
        "/update_topic_names — обновить названия тем (для админов)\n"
        "/admin_report — сводный отчёт по событиям (для админов)"
    )
    await message.answer(help_text, parse_mode="HTML")


@router.message(Command("health"))
async def cmd_health(message: Message):
    """Быстрый health-check."""
    await message.answer("✅ Бот запущен и отвечает. Используйте /debug_info для подробной диагностики.")


@router.message(Command("debug_info"))
async def cmd_debug_info(message: Message):
    """Единая диагностическая команда."""
    from config import ADMIN_IDS
    from utils.topics import get_topics_list_from_db
    import sys

    try:
        me = await message.bot.get_me()
        chat = await message.bot.get_chat(GROUP_ID)
        member = await message.bot.get_chat_member(GROUP_ID, me.id)
        topics = await get_topics_list_from_db()
        is_admin = member.status in ["administrator", "creator"]
        is_forum = getattr(chat, "is_forum", False)

        text = (
            "🔎 <b>Диагностика бота</b>\n\n"
            f"🤖 Бот: @{me.username} (id: <code>{me.id}</code>)\n"
            f"📦 aiogram: <code>{aiogram.__version__}</code>\n"
            f"🐍 Python: <code>{sys.version.split()[0]}</code>\n\n"
            f"👥 Группа: <b>{chat.title}</b> (<code>{chat.id}</code>)\n"
            f"🧵 Форум включён: {'✅' if is_forum else '❌'}\n"
            f"🔐 Права админа у бота: {'✅' if is_admin else '❌'}\n"
            f"📚 Тем в БД: <b>{len(topics)}</b>\n\n"
            f"👤 Ваш id: <code>{message.from_user.id}</code>\n"
            f"🛡 Вы в ADMIN_IDS: {'✅' if message.from_user.id in ADMIN_IDS else '❌'}"
        )
        await message.answer(text, parse_mode="HTML")
    except Exception as e:
        await message.answer(f"❌ Ошибка диагностики: {e}")


@router.message(Command("list_topics"))
async def list_topics(message: Message):
    """Список обнаруженных тем."""
    from utils.topics import get_topics_list_from_db

    topics = await get_topics_list_from_db()

    if not topics:
        await message.answer(
            "❌ Тем не обнаружено.\n\n"
            "📝 Как добавить темы:\n"
            "1. Откройте группу\n"
            "2. Создайте новую тему\n"
            "3. Отправьте сообщение в эту тему\n"
            "4. Бот автоматически обнаружит тему\n"
            "5. Используйте /list_topics снова"
        )
        return

    response = f"✅ Обнаружено {len(topics)} тем:\n\n"
    for topic in topics:
        response += f"📁 {topic['name']}\n"
        response += f"   ID: {topic['message_thread_id']}\n"

    await message.answer(response)


@router.message(Command("update_topic_names"))
@admin_only
async def update_topic_names(message: Message):
    """Обновляет названия тем из контекста группы."""

    from database import get_all_topics

    await message.answer("⏳ Обновляю названия тем...")

    try:
        topics = await get_all_topics()
        updated_count = 0

        for topic in topics:
            if topic["name"].startswith("Тема "):
                logger.info(f"Требуется обновление названия для темы {topic['message_thread_id']}")
                updated_count += 1

        await message.answer(f"✅ Проверено {len(topics)} тем\nОбновлено: {updated_count}")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


@router.callback_query(F.data == "cancel_create")
async def cancel_create(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.answer("Создание мероприятия отменено", show_alert=True)
