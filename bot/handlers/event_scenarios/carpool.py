import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from constants import EVENT_CATEGORY_GROUPS
from keyboards import (
    carpool_keyboard,
    category_groups_keyboard,
    choose_topic_keyboard,
)
from utils.topics import get_topics_list_from_db
from .shared import CreateEvent

logger = logging.getLogger(__name__)
router = Router(name=__name__)


@router.message(CreateEvent.carpool)
async def process_carpool(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Выберите вариант кнопкой ниже.", reply_markup=carpool_keyboard())
        return

    normalized = message.text.lower().strip()
    if normalized not in {"да", "нет", "yes", "no", "y", "n", "1", "0", "true", "false"}:
        await message.answer("Нажмите одну из кнопок: «Да» или «Нет».", reply_markup=carpool_keyboard())
        return

    carpool = normalized in {"да", "yes", "y", "1", "true"}
    await process_carpool_choice(message, state, carpool)


@router.callback_query(CreateEvent.carpool, F.data.in_(["carpool_yes", "carpool_no"]))
async def process_carpool_callback(callback: CallbackQuery, state: FSMContext):
    carpool = callback.data == "carpool_yes"
    await callback.answer("Выбор сохранён")
    await process_carpool_choice(callback.message, state, carpool)


async def process_carpool_choice(message: Message, state: FSMContext, carpool: bool):
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
    await message.answer(
        "📂 Выберите группу категории:",
        reply_markup=category_groups_keyboard(EVENT_CATEGORY_GROUPS),
    )


@router.callback_query(CreateEvent.thread, F.data.startswith("topic_"))
async def process_topic(callback: CallbackQuery, state: FSMContext):
    try:
        thread_id_str = callback.data.split("_")[1]
        thread_id = int(thread_id_str) if thread_id_str != "0" else None

        await state.update_data(thread_id=thread_id)
        await callback.answer("✅ Тема выбрана!")

        await state.set_state(CreateEvent.category)
        await callback.message.answer(
            "📂 Выберите группу категории:",
            reply_markup=category_groups_keyboard(EVENT_CATEGORY_GROUPS),
        )
    except Exception as exc:
        logger.error(f"Ошибка при обработке темы: {exc}")
        await callback.answer("❌ Ошибка! Попробуйте снова.", show_alert=True)
