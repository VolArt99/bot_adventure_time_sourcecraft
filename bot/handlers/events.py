# создание, редактирование, просмотр мероприятий

# ⚠️ ОБНОВЛЕНО: Исправлена работа с темами, добавлена валидация

from aiogram import Router, F, Bot
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
import logging
from datetime import datetime
import pytz
from config import ADMIN_IDS, GROUP_ID, TIMEZONE
from database import create_event, update_event_message_id, get_participants
from utils.topics import get_topics_list_from_db, validate_thread_id
from keyboards import cancel_keyboard, choose_topic_keyboard, event_actions
from texts import format_event_message
from utils.weather import get_weather
from utils.helpers import get_username_by_id

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
    # ⚠️ ОБНОВЛЕНО: Проверка прав организатора
    if message.from_user.id not in ADMIN_IDS:
        await message.answer(
            "❌ У вас нет прав для создания мероприятий.\nОбратитесь к администратору."
        )
        return
    await state.set_state(CreateEvent.title)
    await message.answer(
        "📝 Введите название мероприятия:", reply_markup=cancel_keyboard()
    )


@router.message(CreateEvent.title)
async def process_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(CreateEvent.description)
    await message.answer(
        "📄 Введите описание (или 'пропустить'):", reply_markup=cancel_keyboard()
    )


@router.message(CreateEvent.description)
async def process_description(message: Message, state: FSMContext):
    await state.update_data(
        description=message.text if message.text.lower() != "пропустить" else ""
    )
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
            reply_markup=cancel_keyboard(),
        )
    except ValueError:
        await message.answer("❌ Неверный формат. Используйте ДД.ММ.ГГГГ ЧЧ:ММ")


@router.message(CreateEvent.duration)
async def process_duration(message: Message, state: FSMContext):
    if message.text.lower() == "пропустить":
        duration_minutes = None
    else:
        try:
            hours = float(message.text)
            duration_minutes = int(hours * 60)
        except ValueError:
            await message.answer(
                "❌ Введите число часов (например, 2.5) или 'пропустить':"
            )
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
        "👥 Введите лимит участников (число или 'без лимита'):",
        reply_markup=cancel_keyboard(),
    )


@router.message(CreateEvent.limit)
async def process_limit(message: Message, state: FSMContext):
    if message.text.lower() == "без лимита":
        participant_limit = None
    else:
        try:
            participant_limit = int(message.text)
        except ValueError:
            await message.answer("❌ Введите число или 'без лимита':")
            return
    await state.update_data(participant_limit=participant_limit)
    await state.set_state(CreateEvent.carpool)
    await message.answer(
        "🚗 Нужен карпулинг? (да/нет):", reply_markup=cancel_keyboard()
    )


# ✅ ИСПРАВЛЕННАЯ ФУНКЦИЯ process_carpool() в handlers/events.py


@router.message(CreateEvent.carpool)
async def process_carpool(message: Message, state: FSMContext):
    carpool = message.text.lower() in ["да", "yes", "y", "1", "true"]
    await state.update_data(carpool_enabled=carpool)

    # Получаем темы из БД
    from utils.topics import get_topics_list_from_db

    logger.info("Получение тем для выбора...")
    topics = await get_topics_list_from_db()

    logger.info(f"Доступные темы: {len(topics)}")

    if topics:
        await state.update_data(topics=topics)
        await state.set_state(CreateEvent.thread)
        await message.answer(
            "🗂 Выберите, где опубликовать мероприятие:",
            reply_markup=choose_topic_keyboard(topics),
        )
        return
    else:
        await message.answer(
            "⚠️ Тем не найдено. Опубликуем в основной чат.\n"
            "💡 Совет: Отправьте сообщение в любую тему группы, "
            "и бот её автоматически обнаружит."
        )

    # Если нет тем, пропускаем выбор
    await state.update_data(thread_id=None)
    await state.set_state(CreateEvent.category)
    await message.answer(
        "🏷 Введите категорию мероприятия:\n"
        "Доступные варианты: спорт, прогулки, поездки, игры, культура, еда, обучение",
        reply_markup=cancel_keyboard(),
    )


# ✅ ИСПРАВЛЕННАЯ ФУНКЦИЯ process_topic() в handlers/events.py
@router.callback_query(CreateEvent.thread, F.data.startswith("topic_"))
async def process_topic(callback: CallbackQuery, state: FSMContext):
    try:
        thread_id_str = callback.data.split("_")[1]
        thread_id = int(thread_id_str) if thread_id_str != "0" else None

        await state.update_data(thread_id=thread_id)
        await callback.answer("✅ Тема выбрана!")

        # Удаляем старое сообщение
        try:
            await callback.message.delete()
        except:
            pass

        # Переходим к выбору категории
        await state.set_state(CreateEvent.category)
        await callback.message.answer(
            "📂 Введите категорию мероприятия:\n"
            "Доступные варианты: спорт, прогулки, поездки, игры, культура, еда, обучение",
            reply_markup=cancel_keyboard(),
        )
    except Exception as e:
        logger.error(f"Ошибка при обработке темы: {e}")
        await callback.answer("❌ Ошибка! Попробуйте снова.", show_alert=True)


@router.message(CreateEvent.category)
async def process_category(message: Message, state: FSMContext):
    await state.update_data(category=message.text)
    data = await state.get_data()

    # Получаем погоду
    weather_info = ""
    if data.get("location"):
        weather = await get_weather(city=data["location"])
        if weather:
            weather_info = (
                f"{weather['icon']} {weather['description']}, {weather['temp']}°C"
            )

    # Сохраняем в БД
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
        "category": data.get("category"),
    }
    event_id = await create_event(event_data)

    # Публикуем сообщение в группе
    bot = message.bot
    going_list = []
    waitlist_list = []
    usernames = {
        message.from_user.id: message.from_user.username or str(message.from_user.id)
    }

    event_text = await format_event_message(
        {**event_data, "id": event_id}, going_list, waitlist_list, usernames
    )

    # ⚠️ ОБНОВЛЕНО: Отправка с обработкой ошибок
    try:
        sent_msg = await bot.send_message(
            chat_id=GROUP_ID,
            text=event_text,
            message_thread_id=data.get("thread_id"),
            reply_markup=event_actions(event_id, data.get("carpool_enabled", False)),
            parse_mode="Markdown",
        )
        await update_event_message_id(
            event_id, data.get("thread_id"), sent_msg.message_id
        )

        # ⚠️ НОВОЕ: Планирование напоминаний
        from utils.scheduler import schedule_reminders_for_event

        await schedule_reminders_for_event(event_id, bot)

        await state.clear()
        link = (
            f"https://t.me/c/{str(GROUP_ID).replace('-100', '')}/{sent_msg.message_id}"
        )
        await message.answer(f"✅ Мероприятие создано!\n🔗 {link}")
    except Exception as e:
        logger.error(f"Ошибка публикации: {e}")
        await message.answer(f"❌ Ошибка публикации: {str(e)[:100]}")
