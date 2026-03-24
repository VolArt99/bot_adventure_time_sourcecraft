# создание, редактирование, просмотр мероприятий

from aiogram import Router, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
import re
from datetime import datetime
from database import create_event, get_forum_topics
from keyboards import cancel_keyboard
from utils.weather import get_weather
from config import GROUP_ID

router = Router()

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
    # Проверка, что пользователь - организатор (админ)
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("У вас нет прав для создания мероприятий.")
        return
    await state.set_state(CreateEvent.title)
    await message.answer("Введите название мероприятия:", reply_markup=cancel_keyboard())

# Далее обработчики каждого шага...