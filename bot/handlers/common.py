# команды /start, /help, проверка членства

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from database import get_or_create_user
from config import GROUP_ID

router = Router()

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