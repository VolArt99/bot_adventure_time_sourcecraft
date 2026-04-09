from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from constants import EVENT_CATEGORIES
from database import (
    get_events_for_user_subscriptions,
    get_or_create_user,
    get_topic_name_by_thread_id,
    get_user_category_subscriptions,
    set_user_category_subscriptions,
)
from keyboards import period_keyboard
from texts import format_digest_text
from utils.helpers import get_username_by_id

router = Router(name=__name__)


def _subscriptions_keyboard(selected: list[str]):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    rows = []
    for category in EVENT_CATEGORIES:
        mark = "✅ " if category in selected else ""
        rows.append([InlineKeyboardButton(text=f"{mark}{category.title()}", callback_data=f"sub_toggle_{category}")])

    rows.append([InlineKeyboardButton(text="💾 Сохранить", callback_data="sub_save")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(Command("subscriptions"))
async def cmd_subscriptions(message: Message):
    await get_or_create_user(message.from_user.id, message.from_user.username)
    selected = await get_user_category_subscriptions(message.from_user.id)
    await message.answer(
        "Выберите категории для персонального дайджеста:",
        reply_markup=_subscriptions_keyboard(selected),
    )


@router.callback_query(F.data.startswith("sub_toggle_"))
async def toggle_subscription(callback: CallbackQuery):
    category = callback.data.removeprefix("sub_toggle_")
    selected = await get_user_category_subscriptions(callback.from_user.id)

    if category in selected:
        selected.remove(category)
    else:
        selected.append(category)

    await set_user_category_subscriptions(callback.from_user.id, selected)
    await callback.answer("Подписки обновлены")
    await callback.message.edit_reply_markup(reply_markup=_subscriptions_keyboard(sorted(set(selected))))


@router.callback_query(F.data == "sub_save")
async def save_subscriptions(callback: CallbackQuery):
    selected = await get_user_category_subscriptions(callback.from_user.id)
    if selected:
        await callback.answer("Сохранено")
        await callback.message.answer(f"✅ Подписки сохранены: {', '.join(selected)}")
    else:
        await callback.answer("Сохранено")
        await callback.message.answer("✅ Подписки очищены. Персональный дайджест отключён.")


@router.message(Command("my_digest"))
async def cmd_my_digest(message: Message):
    await message.answer(
        "Выберите период для персонального дайджеста по вашим подпискам:",
        reply_markup=period_keyboard("my_digest"),
    )


@router.callback_query(F.data.startswith("my_digest_"))
async def my_digest_with_period(callback: CallbackQuery):
    period = callback.data.removeprefix("my_digest_")
    events = await get_events_for_user_subscriptions(callback.from_user.id, period=period)

    if not events:
        await callback.message.answer("По вашим подпискам пока нет мероприятий на выбранный период.")
        await callback.answer()
        return

    usernames = {}
    for event in events:
        usernames[event["creator_id"]] = await get_username_by_id(event["creator_id"], callback.bot)
        topic_name = await get_topic_name_by_thread_id(event.get("thread_id"))
        event["topic_name"] = topic_name

    text = format_digest_text(events, usernames, period=period)
    await callback.message.answer(text, parse_mode="HTML", disable_web_page_preview=True)
    await callback.answer()
