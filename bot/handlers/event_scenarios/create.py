from aiogram import F, Router
from datetime import datetime
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.constants import CARPOOL_HELP_TEXT
from bot.filters.registered_user import registered_user_only
from bot.keyboards import cancel_keyboard, skip_field_keyboard, carpool_keyboard
from .shared import CreateEvent, parse_datetime

router = Router(name=__name__)


@router.message(Command("create_event"))
@registered_user_only
async def cmd_create_event(message: Message, state: FSMContext):
    if message.chat.type != "private":
        await message.answer("❌ Команду /create_event нужно запускать в личных сообщениях с ботом.")
        return

    await state.set_state(CreateEvent.title)
    await message.answer("📝 Введите название мероприятия:", reply_markup=cancel_keyboard())


@router.message(CreateEvent.title, ~F.text.startswith("/"))
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
        f"🗓 Введите дату и время (ДД.ММ.ГГГГ ЧЧ:ММ):\nПример: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        reply_markup=cancel_keyboard(),
    )


@router.message(CreateEvent.description, ~F.text.startswith("/"))
async def process_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text if message.text.lower() != "пропустить" else "")
    await state.set_state(CreateEvent.datetime)
    await message.answer(
        f"🗓 Введите дату и время (ДД.ММ.ГГГГ ЧЧ:ММ):\nПример: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        reply_markup=cancel_keyboard(),
    )


@router.message(CreateEvent.datetime, ~F.text.startswith("/"))
async def process_datetime(message: Message, state: FSMContext):
    dt = await parse_datetime(message.text)
    if not dt:
        await message.answer("❌ Неверный формат или дата в прошлом. Используйте ДД.ММ.ГГГГ ЧЧ:ММ")
        return

    await state.update_data(date_time=dt.isoformat())
    await state.set_state(CreateEvent.duration)
    await message.answer(
        "⏱ Введите длительность в часах (или 'пропустить'):\nПример: 2.5",
        reply_markup=skip_field_keyboard("duration"),
    )


@router.callback_query(CreateEvent.duration, F.data == "skip_duration")
async def skip_duration(callback: CallbackQuery, state: FSMContext):
    await state.update_data(duration_minutes=None)
    await state.set_state(CreateEvent.location)
    await callback.answer("Длительность пропущена")
    await callback.message.answer("📍 Введите место проведения:", reply_markup=cancel_keyboard())


@router.message(CreateEvent.duration, ~F.text.startswith("/"))
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


@router.message(CreateEvent.location, ~F.text.startswith("/"))
async def process_location(message: Message, state: FSMContext):
    await state.update_data(location=message.text)
    await state.set_state(CreateEvent.price)
    await message.answer(
        "💰 Введите стоимость:\nОбщая и с человека через пробел (5000 500)\nИли только с человека",
        reply_markup=cancel_keyboard(),
    )


@router.message(CreateEvent.price, ~F.text.startswith("/"))
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
    await callback.message.answer(CARPOOL_HELP_TEXT, reply_markup=carpool_keyboard(), parse_mode="HTML")


@router.message(CreateEvent.limit, ~F.text.startswith("/"))
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
    await message.answer(CARPOOL_HELP_TEXT, reply_markup=carpool_keyboard(), parse_mode="HTML")