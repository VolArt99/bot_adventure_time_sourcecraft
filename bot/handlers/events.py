# создание, редактирование, просмотр мероприятий

from aiogram import Router, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
import logging
from datetime import datetime
import pytz
from config import ADMIN_IDS, GROUP_ID, TIMEZONE
from constants import EVENT_CATEGORIES, CARPOOL_HELP_TEXT
from database import create_event, update_event_message_id, get_topic_name_by_thread_id
from keyboards import (
    cancel_keyboard,
    choose_topic_keyboard,
    event_actions,
    skip_field_keyboard,
    category_keyboard,
)
from texts import format_event_message
from utils.helpers import get_user_mention
from utils.topics import get_topics_list_from_db
from utils.weather import get_weather

logger = logging.getLogger(__name__)
router = Router()
TZ = pytz.timezone(TIMEZONE)


class CreateEvent(StatesGroup):
    title = State()
    description = State()
    datetime = State()
    duration = State()
    location = State()
    price = State()
    limit = State()
    carpool = State()
    thread = State()
    category = State()


@router.message(Command("create_event"))
async def cmd_create_event(message: Message, state: FSMContext):
    if message.chat.type != "private":
        await message.answer("❌ Команду /create_event нужно запускать в личных сообщениях с ботом.")
        return

    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У вас нет прав для создания мероприятий.\nОбратитесь к администратору.")
        return

    await state.set_state(CreateEvent.title)
    await message.answer("📝 Введите название мероприятия:", reply_markup=cancel_keyboard())


@router.message(CreateEvent.title)
async def process_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(CreateEvent.description)
    await message.answer(
        "📄 Введите описание (или 'пропустить'):",
        reply_markup=skip_field_keyboard("description"),
    )

@router.callback_query(CreateEvent.description, F.data == "skip_description")
async def skip_description(callback: CallbackQuery, state: FSMContext):
    await state.update_data(description="")
    await state.set_state(CreateEvent.datetime)
    await callback.answer("Описание пропущено")
    await callback.message.answer(
        "🗓 Введите дату и время (ДД.ММ.ГГГГ ЧЧ:ММ):\nПример: 31.12.2025 18:00",
        reply_markup=cancel_keyboard(),
    )


@router.message(CreateEvent.description)
async def process_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text if message.text.lower() != "пропустить" else "")
    await state.set_state(CreateEvent.datetime)
    await message.answer(
        "🗓 Введите дату и время (ДД.ММ.ГГГГ ЧЧ:ММ):\nПример: 31.12.2025 18:00",
        reply_markup=cancel_keyboard(),
    )


@router.message(CreateEvent.datetime)
async def process_datetime(message: Message, state: FSMContext):
    try:
        dt = datetime.strptime(message.text, "%d.%m.%Y %H:%M")
        dt = TZ.localize(dt)
        if dt < datetime.now(TZ):
            await message.answer("❌ Дата должна быть в будущем. Попробуйте ещё раз:")
            return
        await state.update_data(date_time=dt.isoformat())
        await state.set_state(CreateEvent.duration)
        await message.answer(
            "⏱ Введите длительность в часах (или 'пропустить'):\nПример: 2.5",
            reply_markup=skip_field_keyboard("duration"),
        )
    except ValueError:
        await message.answer("❌ Неверный формат. Используйте ДД.ММ.ГГГГ ЧЧ:ММ")

@router.callback_query(CreateEvent.duration, F.data == "skip_duration")
async def skip_duration(callback: CallbackQuery, state: FSMContext):
    await state.update_data(duration_minutes=None)
    await state.set_state(CreateEvent.location)
    await callback.answer("Длительность пропущена")
    await callback.message.answer("📍 Введите место проведения:", reply_markup=cancel_keyboard())

@router.message(CreateEvent.duration)
async def process_duration(message: Message, state: FSMContext):
    if message.text.lower() == "пропустить":
        duration_minutes = None
    else:
        try:
            duration_minutes = int(float(message.text) * 60)
        except ValueError:
            await message.answer("❌ Введите число часов (например, 2.5) или 'пропустить':")
            return
        
    await state.update_data(duration_minutes=duration_minutes)
    await state.set_state(CreateEvent.location)
    await message.answer("📍 Введите место проведения:", reply_markup=cancel_keyboard())


@router.message(CreateEvent.location)
async def process_location(message: Message, state: FSMContext):
    await state.update_data(location=message.text)
    await state.set_state(CreateEvent.price)
    await message.answer(
        "💰 Введите стоимость:\nОбщая и с человека через пробел (5000 500)\nИли только с человека",
        reply_markup=cancel_keyboard(),
    )


@router.message(CreateEvent.price)
async def process_price(message: Message, state: FSMContext):
    parts = message.text.split()
    total = None
    per_person = None
    if len(parts) == 2:
        try:
            total = float(parts[0])
            per_person = float(parts[1])
        except ValueError:
            await message.answer("❌ Введите числа, например: 5000 500")
            return
    elif len(parts) == 1:
        try:
            per_person = float(parts[0])
        except ValueError:
            await message.answer("❌ Введите число")
            return
    else:
        await message.answer("❌ Введите одно или два числа")
        return
    
    await state.update_data(price_total=total, price_per_person=per_person)
    await state.set_state(CreateEvent.limit)
    await message.answer(
        "👥 Введите лимит участников (число, 'без лимита' или 'пропустить'):",
        reply_markup=skip_field_keyboard("limit"),
    )

@router.callback_query(CreateEvent.limit, F.data == "skip_limit")
async def skip_limit(callback: CallbackQuery, state: FSMContext):
    await state.update_data(participant_limit=None)
    await state.set_state(CreateEvent.carpool)
    await callback.answer("Лимит пропущен")
    await callback.message.answer(CARPOOL_HELP_TEXT, reply_markup=cancel_keyboard(), parse_mode="HTML")

@router.message(CreateEvent.limit)
async def process_limit(message: Message, state: FSMContext):
    if message.text.lower() in {"без лимита", "пропустить"}:
        participant_limit = None
    else:
        try:
            participant_limit = int(message.text)
        except ValueError:
            await message.answer("❌ Введите число, 'без лимита' или 'пропустить':")
            return
        
    await state.update_data(participant_limit=participant_limit)
    await state.set_state(CreateEvent.carpool)
    await message.answer(CARPOOL_HELP_TEXT, reply_markup=cancel_keyboard(), parse_mode="HTML")



# ✅ ИСПРАВЛЕННАЯ ФУНКЦИЯ process_carpool() в handlers/events.py


@router.message(CreateEvent.carpool)
async def process_carpool(message: Message, state: FSMContext):
    carpool = message.text.lower() in ["да", "yes", "y", "1", "true"]
    await state.update_data(carpool_enabled=carpool)

    topics = await get_topics_list_from_db()

    if topics:
        await state.set_state(CreateEvent.thread)
        await message.answer("🗂 Выберите, где опубликовать мероприятие:", reply_markup=choose_topic_keyboard(topics))
        return

    await message.answer(
        "⚠️ Тем не найдено. Опубликуем в основной чат.\n"
        "💡 Отправьте сообщение в любую тему группы, и бот её автоматически обнаружит."
    )
    await state.update_data(thread_id=None)
    await state.set_state(CreateEvent.category)
    await message.answer("📂 Выберите категорию мероприятия:", reply_markup=category_keyboard(EVENT_CATEGORIES))


@router.callback_query(CreateEvent.thread, F.data.startswith("topic_"))
async def process_topic(callback: CallbackQuery, state: FSMContext):
    try:
        thread_id_str = callback.data.split("_")[1]
        thread_id = int(thread_id_str) if thread_id_str != "0" else None

        await state.update_data(thread_id=thread_id)
        await callback.answer("✅ Тема выбрана!")

        await state.set_state(CreateEvent.category)
        await callback.message.answer("📂 Выберите категорию мероприятия:", reply_markup=category_keyboard(EVENT_CATEGORIES))
    except Exception as exc:
        logger.error(f"Ошибка при обработке темы: {exc}")
        await callback.answer("❌ Ошибка! Попробуйте снова.", show_alert=True)


@router.message(CreateEvent.category)
async def process_category(message: Message, state: FSMContext):
    category_text = (message.text or "").strip().lower()
    if category_text not in EVENT_CATEGORIES:
        await message.answer("❌ Выберите категорию из кнопок ниже.", reply_markup=category_keyboard(EVENT_CATEGORIES))
        return

    await finalize_event_creation(message, state, category_text)


@router.callback_query(CreateEvent.category, F.data.startswith("category_"))
async def process_category_callback(callback: CallbackQuery, state: FSMContext):
    category_text = callback.data.replace("category_", "", 1)
    if category_text not in EVENT_CATEGORIES:
        await callback.answer("Категория недоступна", show_alert=True)
        return

    await callback.answer("Категория выбрана")
    await finalize_event_creation(callback.message, state, category_text)


async def finalize_event_creation(message: Message, state: FSMContext, category_value: str):
    await state.update_data(category=category_value)
    data = await state.get_data()

    weather_info = ""
    if data.get("location"):
        weather = await get_weather(city=data["location"])
        if weather:
            weather_info = f"{weather['icon']} {weather['description']}, {weather['temp']}°C"

    event_data = {
        "title": data["title"],
        "description": data.get("description"),
        "date_time": data["date_time"],
        "duration_minutes": data.get("duration_minutes"),
        "location": data.get("location"),
        "price_total": data.get("price_total"),
        "price_per_person": data.get("price_per_person"),
        "participant_limit": data.get("participant_limit"),
        "thread_id": data.get("thread_id"),
        "creator_id": message.from_user.id,
        "weather_info": weather_info,
        "carpool_enabled": data.get("carpool_enabled", False),
        "category": category_value,
    }
    event_id = await create_event(event_data)

    
    bot = message.bot
    organizer_mention = await get_user_mention(message.from_user.id, bot)
    mentions = {message.from_user.id: organizer_mention}
    topic_name = await get_topic_name_by_thread_id(data.get("thread_id"))

    event_text = await format_event_message(
        {**event_data, "id": event_id},
        [],
        [],
        mentions,
        topic_name=topic_name,
        organizer_mention=organizer_mention,
    )

    try:
        sent_msg = await bot.send_message(
            chat_id=GROUP_ID,
            text=event_text,
            message_thread_id=data.get("thread_id"),
            reply_markup=event_actions(event_id, data.get("carpool_enabled", False)),
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
        await update_event_message_id(event_id, data.get("thread_id"), sent_msg.message_id)

        from utils.scheduler import schedule_reminders_for_event

        await schedule_reminders_for_event(event_id, bot)

        await state.clear()
        link = f"https://t.me/c/{str(GROUP_ID).replace('-100', '')}/{sent_msg.message_id}"
        await message.answer(f"✅ Мероприятие создано!\n🧵 Тема: {topic_name or 'Основной чат'}\n🔗 {link}")
    except Exception as exc:
        logger.error(f"Ошибка публикации: {exc}")
        await message.answer(f"❌ Ошибка публикации: {str(exc)[:200]}")
