# команды /start, /help, проверка членства

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from database import get_or_create_user
from config import BOT_TOKEN, GROUP_ID
import aiohttp
import json
import aiogram  # ⚠️ ДОБАВЛЕНО: импорт для доступа к __version__

router = Router()

@router.message(Command("test_chat"))
async def cmd_test_chat(message: Message):
    """Тест связи с группой."""
    try:
        chat = await message.bot.get_chat(GROUP_ID)
        is_forum = getattr(chat, 'is_forum', False)
        
        text = (
            f"✅ **Информация о группе:**\n\n"
            f"📛 Название: {chat.title}\n"
            f"🆔 ID: `{chat.id}`\n"
            f"📋 Тип: {chat.type}\n"
            f"📁 Форум: {'✅ Да' if is_forum else '❌ Нет'}\n\n"
            f"{'✅ Группа готова к работе с темами.' if is_forum else '⚠️ Включите темы в настройках группы!'}\n"
        )
        await message.answer(text, parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")

@router.message(Command("test_bot_rights"))
async def cmd_test_bot_rights(message: Message):
    """Проверка прав бота в группе."""
    try:
        chat = await message.bot.get_chat(GROUP_ID)
        member = await message.bot.get_chat_member(GROUP_ID, message.bot.id)
        
        is_admin = member.status in ['administrator', 'creator']
        
        text = (
            f"🤖 **Статус бота в группе:**\n\n"
            f"📛 Группа: {chat.title}\n"
            f"👤 Статус: {member.status}\n"
            f"🔑 Администратор: {'✅ Да' if is_admin else '❌ Нет'}\n"
        )
        
        if is_admin and hasattr(member, 'privileges'):
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

@router.message(Command("test_topics"))
async def cmd_test_topics(message: Message):
    """Тест получения тем форума."""
    try:
        # Проверка типа группы
        chat = await message.bot.get_chat(GROUP_ID)
        is_forum = getattr(chat, 'is_forum', False)
        
        if not is_forum:
            await message.answer(
                "❌ **Группа не является форумом!**\n\n"
                "Включите темы: Настройки группы → Тип группы → Форум",
                parse_mode="Markdown"
            )
            return
        
        # ⚠️ Получение тем
        topics = await message.bot.get_forum_topics(GROUP_ID)
        
        if not topics:
            await message.answer(
                "⚠️ **Темы не найдены!**\n\n"
                "Создайте хотя бы одну тему вручную в группе.",
                parse_mode="Markdown"
            )
            return
        
        text = f"✅ **Найдено тем: {len(topics)}**\n\n"
        for topic in topics[:10]:
            text += f"📁 `{topic.message_thread_id}` — {topic.name}\n"
        
        if len(topics) > 10:
            text += f"\n... и ещё {len(topics) - 10} тем"
        
        await message.answer(text, parse_mode="Markdown")
        
    except AttributeError as e:
        if 'get_forum_topics' in str(e):
            await message.answer(
                "❌ **Ошибка версии aiogram!**\n\n"
                f"Ваша ошибка: `{str(e)}`\n\n"
                "**Решение:**\n"
                "1. Остановите бота\n"
                "2. `pip install --upgrade aiogram`\n"
                "3. Удалите папки `__pycache__`\n"
                "4. Перезапустите бота",
                parse_mode="Markdown"
            )
        else:
            await message.answer(f"❌ Ошибка: {str(e)}")
    except Exception as e:
        await message.answer(f"❌ Ошибка API: {str(e)[:200]}")

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
        "Доступные команды:\n"
        "/create_event - создать мероприятие (только для организаторов)\n"
        "/my_events - мои мероприятия\n"
        "/digest - дайджест мероприятий на неделю\n"
        "/help - это сообщение"
    )
    await message.answer(help_text)

@router.callback_query(F.data == "cancel_create")
async def cancel_create(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.answer("Создание мероприятия отменено", show_alert=True)