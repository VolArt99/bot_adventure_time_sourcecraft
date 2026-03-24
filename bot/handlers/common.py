# команды /start, /help, проверка членства

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from database import get_or_create_user
from config import BOT_TOKEN, GROUP_ID
import aiohttp
import json

router = Router()

@router.message(Command("test_chat"))
async def test_chat(message: Message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChat"
    params = {"chat_id": GROUP_ID}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=params) as resp:
            result = await resp.json()
            if result.get("ok"):
                chat_info = result.get("result")
                await message.answer(f"✅ Группа: {chat_info.get('title')}, тип: {chat_info.get('type')}")
            else:
                await message.answer(f"❌ Ошибка: {result.get('description')}")

@router.message(Command("test_topics"))
async def test_topics(message: Message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getForumTopics"
    params = {"chat_id": GROUP_ID}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=params) as resp:
            result = await resp.json()
            if result.get("ok"):
                topics = result.get("result", {}).get("topics", [])
                await message.answer(f"✅ Найдено тем: {len(topics)}")
                for topic in topics[:5]:
                    await message.answer(f"Тема: {topic['name']}, ID: {topic['message_thread_id']}")
            else:
                await message.answer(f"❌ Ошибка API: {result.get('description')}")


@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    await get_or_create_user(user_id, username)
    await message.answer("Привет! Я бот для управления мероприятиями в группе. Для начала работы добавьте меня в группу и назначьте администратором с правами на отправку сообщений в темы.")

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