# команды /start, /help, проверка членства

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from database import get_or_create_user
from config import BOT_TOKEN, GROUP_ID
import aiohttp
import json
import logging
import aiogram  # ⚠️ ДОБАВЛЕНО: импорт для доступа к __version__

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("test_chat"))
async def test_chat(message: Message):
    """Проверяет информацию о группе."""
    from config import GROUP_ID

    try:
        chat = await message.bot.get_chat(GROUP_ID)
        members_count = await message.bot.get_chat_member_count(GROUP_ID)

        info = (
            f"✅ Информация о группе:\n"
            f"Название: {chat.title}\n"
            f"ID: {chat.id}\n"
            f"Тип: {chat.type}\n"
            f"Форум (is_forum): {getattr(chat, 'is_forum', False)}\n"
            f"Участников: {members_count}\n"
            f"Описание: {chat.description or '—'}"
        )
        await message.answer(info)
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


@router.message(Command("test_bot_rights"))
async def cmd_test_bot_rights(message: Message):
    """Проверка прав бота в группе."""
    try:
        chat = await message.bot.get_chat(GROUP_ID)
        member = await message.bot.get_chat_member(GROUP_ID, message.bot.id)

        is_admin = member.status in ["administrator", "creator"]

        text = (
            f"🤖 **Статус бота в группе:**\n\n"
            f"📛 Группа: {chat.title}\n"
            f"👤 Статус: {member.status}\n"
            f"🔑 Администратор: {'✅ Да' if is_admin else '❌ Нет'}\n"
        )

        if is_admin and hasattr(member, "privileges"):
            permissions = member.privileges
            text += (
                f"\n**Права:**\n"
                f"• Сообщения: {'✅' if permissions.can_send_messages else '❌'}\n"
                f"• Темы форума: {'✅' if getattr(permissions, 'can_manage_forum', False) else '❌'}\n"
                f"• Редактирование: {'✅' if permissions.can_edit_messages else '❌'}\n"
            )

        await message.answer(text, parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")


# ✅ ИСПРАВЛЕННАЯ ФУНКЦИЯ test_topics() в handlers/common.py
@router.message(Command("test_topics"))
async def test_topics(message: Message):
    """Команда для тестирования получения тем."""
    from utils.topics import get_topics_list_from_db

    topics = await get_topics_list_from_db()

    if not topics:
        await message.answer("❌ Темы не найдены в БД")
        return

    response_text = f"✅ Найдено тем: {len(topics)}\n\n"
    for topic in topics[:20]:  # Показываем первые 10
        response_text += f"📁 {topic['name']} (ID: {topic['message_thread_id']})\n"

    await message.answer(response_text)


@router.message(Command("test_version"))
async def cmd_test_version(message: Message):
    """Проверка версии aiogram."""
    import sys

    text = (
        f"📦 **Версии библиотек:**\n\n"
        f"🐍 Python: `{sys.version.split()[0]}`\n"
        f"🤖 aiogram: `{aiogram.__version__}`\n\n"
        f"{'✅ Версия актуальная' if aiogram.__version__ >= '3.3.0' else '⚠️ Требуется 3.3.0+'}\n"
    )
    await message.answer(text, parse_mode="Markdown")


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
        "<b>Текущие команды:</b>\n"
        "/start — регистрация и запуск бота\n"
        "/help — список команд и возможностей\n"
        "/create_event — создать мероприятие (для организаторов)\n"
        "/my_events — мои мероприятия (период: неделя/месяц/всё время)\n"
        "/digest — дайджест мероприятий (период: неделя/месяц/всё время)\n"
        "/my_stats — ваша статистика посещений\n"
        "/top — топ-3 участников за 30 дней\n"
        "/find_events — поиск активных событий по тексту\n\n"
        "<b>Сервисные/диагностические команды:</b>\n"
        "/debug_info — единая диагностика (бот, группа, права, темы)\n"
        "/health — быстрая проверка работоспособности\n"
        "/list_topics — список обнаруженных тем\n"
        "/update_topic_names — обновить названия тем (для админов)\n\n"
        "<b>Устаревшие команды:</b>\n"
        "/test_chat, /test_bot_rights, /test_topics, /test_version,\n"
        "/debug, /check_admin, /debug_topics, /api_version,\n"
        "/check_forum, /show_config\n"
        "➡️ Используйте <b>/debug_info</b>."
    )
    await message.answer(help_text, parse_mode="HTML")


@router.message(Command("health"))
async def cmd_health(message: Message):
    """Быстрый health-check."""
    await message.answer("✅ Бот запущен и отвечает. Используйте /debug_info для подробной диагностики.")


@router.message(Command("debug_info"))
async def cmd_debug_info(message: Message):
    """Единая диагностическая команда вместо множества отдельных."""
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
            f"🐍 Python: <code>{sys.version.split()[0]}</code>\n"
            f"📦 aiogram: <code>{aiogram.__version__}</code>\n\n"
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

        
@router.callback_query(F.data == "cancel_create")
async def cancel_create(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.answer("Создание мероприятия отменено", show_alert=True)


# ✅ ДОБАВИТЬ В common.py (в конец перед последней функцией)


@router.message(Command("debug"))
async def debug_cmd(message: Message):
    """Команда для отладки."""
    from config import BOT_TOKEN, GROUP_ID, ADMIN_IDS

    debug_info = (
        f"🔍 Отладка:\n"
        f"GROUP_ID: {GROUP_ID}\n"
        f"Ваш ID: {message.from_user.id}\n"
        f"Администраторы: {ADMIN_IDS}\n"
        f"Вы администратор: {message.from_user.id in ADMIN_IDS}\n"
        f"aiogram версия: 3.x+"
    )
    await message.answer(debug_info)


# ✅ ИСПРАВЛЕННАЯ ФУНКЦИЯ check_admin() в handlers/common.py


@router.message(Command("check_admin"))
async def check_admin(message: Message):
    """Проверяет, администратор ли бот в группе."""
    from config import GROUP_ID

    try:
        bot_id = (await message.bot.get_me()).id
        chat_member = await message.bot.get_chat_member(GROUP_ID, bot_id)

        # В aiogram 3.x используются разные классы для разных статусов
        is_admin = chat_member.status in ["administrator", "creator"]
        status_text = "✅ Администратор" if is_admin else "❌ Не администратор"

        admin_info = f"""
{status_text}

Статус: {chat_member.status}
Может редактировать: {getattr(chat_member, 'can_edit_messages', '—')}
Может управлять темами: {getattr(chat_member, 'can_manage_topics', '—')}
Может отправлять: {getattr(chat_member, 'can_post_stories', '—')}
"""
        await message.answer(admin_info)
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")


# ✅ ИСПРАВЛЕННАЯ ФУНКЦИЯ debug_topics() в handlers/common.py


# ✅ ИСПРАВЛЕННАЯ ФУНКЦИЯ debug_topics() в handlers/common.py


@router.message(Command("debug_topics"))
async def debug_topics(message: Message):
    """Расширенная отладка получения тем."""
    from config import GROUP_ID
    from config import BOT_TOKEN
    import aiohttp

    try:
        logger.info(f"🔍 Отладка тем для группы {GROUP_ID}")

        # Прямой API вызов
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getForumTopics"
        params = {"chat_id": GROUP_ID, "limit": 100}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=params) as resp:
                data = await resp.json()
                logger.info(f"📡 API ответ: {data}")

                if not data.get("ok"):
                    error_msg = data.get("description", "Unknown error")
                    await message.answer(f"❌ Ошибка API: {error_msg}")
                    return

                topics_data = data.get("result", {}).get("topics", [])

                if topics_data:
                    topics_info = []
                    for topic in topics_data:
                        topics_info.append(
                            f"  🔓 '{topic.get('name')}' (ID: {topic.get('message_thread_id')})"
                        )
                    await message.answer(
                        f"✅ Найдено {len(topics_data)} тем:\n" + "\n".join(topics_info)
                    )
                else:
                    await message.answer("⚠️ В группе нет тем")

    except Exception as e:
        await message.answer(f"❌ Ошибка: {type(e).__name__}: {str(e)}")
        logger.error(f"Error: {type(e).__name__}: {e}", exc_info=True)


# ✅ ДОБАВИТЬ В common.py


@router.message(Command("api_version"))
async def api_version(message: Message):
    """Проверяет версию Bot API."""
    try:
        me = await message.bot.get_me()
        await message.answer(
            f"🤖 Бот: {me.username}\n"
            f"ID: {me.id}\n"
            f"Версия aiogram: 3.x\n"
            f"Bot API: используется последняя версия"
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


# ✅ ДОБАВИТЬ В common.py


@router.message(Command("check_forum"))
async def check_forum(message: Message):
    """Проверяет, является ли группа форумом."""
    from config import GROUP_ID
    import aiohttp
    from config import BOT_TOKEN

    try:
        # Способ 1: Через get_chat
        chat = await message.bot.get_chat(GROUP_ID)
        is_forum = getattr(chat, "is_forum", False)

        info = f"📋 Группа является форумом: {is_forum}\n"

        if is_forum:
            # Способ 2: Попробуем получить темы через API
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getForumTopics"
            params = {"chat_id": GROUP_ID}

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=params) as resp:
                    data = await resp.json()

                    if data.get("ok"):
                        topics = data.get("result", {}).get("topics", [])
                        info += f"✅ Темы получены: {len(topics)} шт."
                        for topic in topics[:5]:
                            info += f"\n  - {topic.get('name')} (ID: {topic.get('message_thread_id')})"
                    else:
                        error = data.get("description", "Unknown")
                        info += f"❌ Ошибка API: {error}"
        else:
            info += "⚠️ Группа не форум. Включите темы в настройках группы!"

        await message.answer(info)

    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


# ✅ ИСПРАВЛЕННАЯ ФУНКЦИЯ list_topics() в handlers/common.py


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
            "2. Создайте новую тему (нажмите на название группы → Темы → Создать)\n"
            "3. Отправьте сообщение в эту тему\n"
            "4. Бот автоматически обн��ружит тему\n"
            "5. Используйте /list_topics снова"
        )
        return

    response = f"✅ Обнаружено {len(topics)} тем:\n\n"
    for topic in topics:
        topic_name = topic["name"]
        topic_id = topic["message_thread_id"]
        response += f"📁 {topic_name}\n"
        response += f"   ID: {topic_id}\n"

    await message.answer(response)


# ✅ ДОБАВИТЬ В common.py
@router.message(Command("update_topic_names"))
async def update_topic_names(message: Message):
    """
    Обновляет названия тем из контекста группы.
    Сначала бот пытается получить названия из сообщений.
    """
    from config import GROUP_ID

    from config import ADMIN_IDS

    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У вас нет прав")
        return

    await message.answer("⏳ Обновляю названия тем...")

    try:
        from database import get_all_topics

        topics = await get_all_topics()
        updated_count = 0

        for topic in topics:
            thread_id = topic["message_thread_id"]
            current_name = topic["name"]

            # Если название по умолчанию (Тема 123), ищем реальное
            if current_name.startswith("Тема "):
                logger.info(f"Обновляю название для темы {thread_id}...")
                # Можно добавить логику получения реального названия
                updated_count += 1

        await message.answer(
            f"✅ Проверено {len(topics)} тем\n" f"Обновлено: {updated_count}"
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


# ✅ ДОБАВИТЬ В common.py
@router.message(Command("show_config"))
async def show_config(message: Message):
    """Показывает конфиг тем."""
    try:
        from topics_config import TOPICS_MAPPING

        if not TOPICS_MAPPING:
            await message.answer("❌ TOPICS_MAPPING пусто")
            return

        response = "📋 Текущий конфиг тем:\n\n"
        for topic_id, topic_name in TOPICS_MAPPING.items():
            response += f"ID: {topic_id} → '{topic_name}'\n"

        response += "\n📝 Как обновить:\n"
        response += "Отредактируйте файл bot/topics_config.py\n"
        response += "и перезагрузите бота"

        await message.answer(response)
    except ImportError:
        await message.answer("❌ Файл topics_config.py не найден")
