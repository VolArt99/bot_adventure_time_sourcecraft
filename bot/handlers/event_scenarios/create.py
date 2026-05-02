from aiogram import F, Router
from datetime import datetime
import asyncio
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.constants import CARPOOL_HELP_TEXT
from bot.filters.registered_user import registered_user_only
from bot.keyboards import cancel_keyboard, skip_field_keyboard, carpool_keyboard, event_price_mode_keyboard
from .shared import CreateEvent, parse_datetime
from bot.utils.ui import err, delete_message_later, safe_delete_bot_message

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
        await message.answer(
            "❌ Неверный формат или дата в прошлом.\n"
            "Используйте: ДД.ММ.ГГГГ ЧЧ:ММ\n"
            "Примеры: 25.05.2026 19:30, 01.06.2026 10:00"
        )
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
            sent = await message.answer(err("Неверный формат.\nПример: 2 или 2.5\nИли напишите: пропустить"))
            asyncio.create_task(delete_message_later(message.bot, sent.chat.id, sent.message_id, 25))
            return

    await state.update_data(duration_minutes=duration_minutes)
    await state.set_state(CreateEvent.location)
    await message.answer("📍 Введите место проведения:", reply_markup=cancel_keyboard())


@router.message(CreateEvent.location, ~F.text.startswith("/"))
async def process_location(message: Message, state: FSMContext):
    await state.update_data(location=message.text)
    await state.set_state(CreateEvent.price_mode)
    await message.answer(
        "💰 Выберите формат стоимости мероприятия:",
        reply_markup=event_price_mode_keyboard(),
    )


@router.callback_query(CreateEvent.price_mode, F.data.startswith("price_mode_"))
async def process_price_mode(callback: CallbackQuery, state: FSMContext):
    mode = callback.data.removeprefix("price_mode_")
    await state.update_data(price_mode=mode)
    if mode == "free":
        await state.update_data(price_total=None, price_per_person=None)
        await state.set_state(CreateEvent.limit)
        await callback.message.answer(
            "👥 Введите лимит участников (число, 'без лимита' или 'пропустить'):",
            reply_markup=skip_field_keyboard("limit"),
        )
        try:
            await safe_delete_bot_message(callback.message)
        except Exception:
            pass
        await callback.answer("Бесплатно")
        return

    await state.set_state(CreateEvent.price)
    if mode == "total":
        prompt = "💰 Введите общую сумму.\nПример: 5000"
    else:
        prompt = "💰 Введите сумму с человека.\nПример: 500"
    await callback.message.answer(prompt, reply_markup=cancel_keyboard())
    try:
        await safe_delete_bot_message(callback.message)
    except Exception:
        pass
    await callback.answer()


@router.message(CreateEvent.price, ~F.text.startswith("/"))
async def process_price(message: Message, state: FSMContext):
    data = await state.get_data()
    mode = data.get("price_mode")
    try:
        amount = float(message.text.replace(",", "."))
    except ValueError:
        sent = await message.answer(err("Неверный формат.\nВведите число, пример: 500"))
        asyncio.create_task(delete_message_later(message.bot, sent.chat.id, sent.message_id, 25))
        return
    if amount < 0:
        await message.answer("❌ Сумма не может быть отрицательной.")
        return

    total = amount if mode == "total" else None
    per_person = amount if mode == "person" else None

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