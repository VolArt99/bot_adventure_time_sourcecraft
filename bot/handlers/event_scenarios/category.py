from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.constants import EVENT_CATEGORIES, EVENT_CATEGORY_GROUPS
from bot.keyboards import category_groups_keyboard, category_subgroups_keyboard
from bot.utils.callbacks import finalize_callback
from bot.utils.ui import answer_private_intermediate
from bot.utils.callback_policy import CALLBACK_DELETE_WIZARD_MESSAGE
from .shared import CreateEvent, finalize_event_creation

router = Router(name=__name__)


@router.message(CreateEvent.category)
async def process_category(message: Message, state: FSMContext):
    await answer_private_intermediate(
        message,
        state,
        "❌ Выбор категорий теперь только через кнопки ниже.",
        reply_markup=category_groups_keyboard(EVENT_CATEGORY_GROUPS),
    )


@router.callback_query(CreateEvent.category, F.data.startswith("category_group_"))
async def open_category_group(callback: CallbackQuery, state: FSMContext):
    group_key = callback.data.replace("category_group_", "", 1)
    if group_key not in EVENT_CATEGORY_GROUPS:
        await finalize_callback(callback, "Группа недоступна", show_alert=True)
        return

    data = await state.get_data()
    selected_categories = data.get("selected_categories", [])
    await state.update_data(active_category_group=group_key)
    await answer_private_intermediate(
        callback.message,
        state,
        f"Выберите подкатегории в группе «{EVENT_CATEGORY_GROUPS[group_key]['title']}». "
        f"Можно выбрать несколько.",
        reply_markup=category_subgroups_keyboard(
            group_key, EVENT_CATEGORY_GROUPS, selected_categories
        ),
    )
    await finalize_callback(callback, "Группа открыта", delete_message=CALLBACK_DELETE_WIZARD_MESSAGE)


@router.callback_query(CreateEvent.category, F.data.startswith("category_toggle_"))
async def toggle_category(callback: CallbackQuery, state: FSMContext):
    category_value = callback.data.replace("category_toggle_", "", 1)
    if category_value not in EVENT_CATEGORIES:
        await finalize_callback(callback, "Подкатегория недоступна", show_alert=True)
        return

    data = await state.get_data()
    active_group = data.get("active_category_group")
    if not active_group:
        await finalize_callback(callback, "Сначала выберите группу", show_alert=True)
        return

    selected_categories = data.get("selected_categories", [])
    if category_value in selected_categories:
        selected_categories.remove(category_value)
    else:
        selected_categories.append(category_value)

    await state.update_data(selected_categories=selected_categories)
    await finalize_callback(callback, "Список обновлён")
    await callback.message.edit_reply_markup(
        reply_markup=category_subgroups_keyboard(
            active_group, EVENT_CATEGORY_GROUPS, selected_categories
        )
    )


@router.callback_query(CreateEvent.category, F.data == "category_back")
async def back_to_category_groups(callback: CallbackQuery, state: FSMContext):
    await answer_private_intermediate(
        callback.message,
        state,
        "📂 Выберите группу категории:",
        reply_markup=category_groups_keyboard(EVENT_CATEGORY_GROUPS),
    )
    await finalize_callback(callback, delete_message=CALLBACK_DELETE_WIZARD_MESSAGE)


@router.callback_query(CreateEvent.category, F.data == "category_done")
async def finish_categories(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected_categories = data.get("selected_categories", [])
    if not selected_categories:
        await finalize_callback(callback, "Выберите хотя бы одну подкатегорию", show_alert=True)
        return

    await finalize_event_creation(
        callback.message,
        state,
        ",".join(selected_categories),
        creator_user_id=callback.from_user.id,
    )
    await finalize_callback(callback, "Категории сохранены", delete_message=CALLBACK_DELETE_WIZARD_MESSAGE)
