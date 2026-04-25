from __future__ import annotations

from datetime import datetime, timezone
import logging

import aiogram
from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.config import (
    ADMIN_DAILY_COMMAND_LIMIT,
    ADMIN_IDS,
    GROUP_ID,
    MEMBER_DAILY_COMMAND_LIMIT,
    OUTSIDER_START_DAILY_LIMIT,
    OWNER_ID,
)
from bot.database import (
    add_pending_user,
    approve_pending_user,
    delete_pending_user,
    get_command_usage_summary,
    get_intro_members_statuses,
    get_or_create_user,
    get_pending_intro_members,
    get_pending_user,
    is_member_approved,
    update_intro_status,
    upsert_approved_member,
)
from bot.filters.admin import admin_only
from bot.filters.command_access import restricted_command
from bot.keyboards import (
    intro_status_keyboard,
    onboarding_start_keyboard,
    rules_ack_keyboard,
)
from bot.texts import GROUP_RULES_TEXT, ONBOARDING_WELCOME_TEXT

from .services import extract_command, is_user_in_group, notify_owner_about_request
from .views import build_help_text

logger = logging.getLogger(__name__)
router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    full_name = " ".join(filter(None, [message.from_user.first_name, message.from_user.last_name])).strip()
    await get_or_create_user(user_id, username)
    if await is_user_in_group(message):
        await upsert_approved_member(user_id, username, full_name, intro_status="completed")
        await message.answer(
            "👋 С возвращением! Вы уже состоите в группе, поэтому заявка не требуется.\n"
            "Используйте /help для списка команд."
        )
        return

    await message.answer(ONBOARDING_WELCOME_TEXT, reply_markup=onboarding_start_keyboard())


@router.callback_query(F.data == "onboarding_start")
async def onboarding_start(callback: CallbackQuery):
    await callback.message.answer(GROUP_RULES_TEXT, reply_markup=rules_ack_keyboard())
    await callback.answer()


@router.callback_query(F.data == "rules_ack")
async def rules_ack(callback: CallbackQuery):
    user = callback.from_user
    full_name = " ".join(filter(None, [user.first_name, user.last_name])).strip()
    if await is_user_in_group(callback.message):
        await upsert_approved_member(user.id, user.username, full_name, intro_status="completed")
        await callback.message.answer("✅ Правила приняты. Вы уже участник группы, доступ открыт.")
    else:
        await add_pending_user(user.id, user.username, full_name)
        await notify_owner_about_request(callback)
        await callback.message.answer("✅ Правила приняты. Заявка отправлена владельцу на проверку.")
    await callback.answer()


@router.message(StateFilter(None), F.chat.type == "private", ~F.text.startswith("/"))
async def onboarding_guard(message: Message):
    command = extract_command(message)
    if command:
        return

    approved = await is_member_approved(message.from_user.id)
    if approved:
        return

    pending = await get_pending_user(message.from_user.id)
    if pending:
        await message.answer("⏳ Ваша заявка уже ожидает решения владельца.")
        return

    await message.answer(
        "Чтобы продолжить, нажмите «Старт», затем «Правила изучил(а) ❤️».\n"
        "Любые другие сообщения до этого шага недоступны.",
        reply_markup=onboarding_start_keyboard(),
    )


@router.callback_query(F.data.startswith("approve_user_"))
async def owner_approve_user(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID:
        await callback.answer("Недостаточно прав", show_alert=True)
        return

    user_id = int(callback.data.rsplit("_", 1)[-1])
    pending = await approve_pending_user(user_id)
    if not pending:
        await callback.answer("Заявка не найдена", show_alert=True)
        return

    try:
        invite = await callback.bot.create_chat_invite_link(chat_id=GROUP_ID, member_limit=1)
        await callback.bot.send_message(
            user_id,
            f"✅ Ваша заявка одобрена. Ссылка для входа в группу:\n{invite.invite_link}",
        )
    except (TelegramForbiddenError, TelegramBadRequest) as exc:
        logger.warning(
            "invite_send_failed user_id=%s command=%s event_id=%s error=%s",
            user_id,
            "approve_user",
            callback.id,
            type(exc).__name__,
        )

    await callback.message.edit_text(f"✅ Пользователь {user_id} одобрен и перенесён в контроль «Рассказа о себе».")
    await callback.answer("Одобрено")


@router.callback_query(F.data.startswith("reject_user_"))
async def owner_reject_user(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID:
        await callback.answer("Недостаточно прав", show_alert=True)
        return

    user_id = int(callback.data.rsplit("_", 1)[-1])
    await delete_pending_user(user_id)
    try:
        await callback.bot.send_message(user_id, "❌ К сожалению, заявка на вступление отклонена.")
    except (TelegramForbiddenError, TelegramBadRequest) as exc:
        logger.info(
            "reject_notify_skipped user_id=%s command=%s event_id=%s error=%s",
            user_id,
            "reject_user",
            callback.id,
            type(exc).__name__,
        )

    await callback.message.edit_text(f"❌ Заявка пользователя {user_id} отклонена.")
    await callback.answer("Отклонено")


@router.message(Command("pending_intro"))
async def cmd_pending_intro(message: Message):
    if message.from_user.id != OWNER_ID:
        await message.answer("❌ Эта команда доступна только владельцу.")
        return

    pending_members = await get_pending_intro_members()
    if not pending_members:
        await message.answer("✅ Нет участников с незавершённым «Рассказом о себе».")
        return

    await message.answer(f"📋 В ожидании «Рассказа о себе»: {len(pending_members)}")
    for member in pending_members:
        username = f"@{member['username']}" if member.get("username") else "—"
        full_name = member.get("full_name") or "—"
        await message.answer(
            f"• ID: {member['user_id']}\n• Имя: {full_name}\n• Username: {username}",
            reply_markup=intro_status_keyboard(member["user_id"]),
        )


@router.message(Command("list_intro"))
async def cmd_list_intro(message: Message):
    if message.from_user.id != OWNER_ID:
        await message.answer("❌ Эта команда доступна только владельцу.")
        return

    members = await get_intro_members_statuses()
    if not members:
        await message.answer("Пока нет одобренных участников.")
        return

    now = datetime.now(timezone.utc)
    lines = ["📊 Контроль «Рассказа о себе»:"]
    for m in members:
        join_date = m.get("join_date")
        if isinstance(join_date, str):
            join_dt = datetime.fromisoformat(join_date.replace("Z", "+00:00"))
        else:
            join_dt = join_date
        days_passed = (now - join_dt).days if join_dt else 0
        days_left = max(0, 7 - days_passed)
        if days_passed <= 7:
            state = f"🟢 Всё хорошо (Осталось {days_left} дн.)"
        elif m.get("intro_status") == "pending":
            state = "🔴 Просрочено! Требуется проверка."
        else:
            state = "✅ Выполнено"

        username = f"@{m['username']}" if m.get("username") else "—"
        lines.append(f"• {m.get('full_name') or '—'} ({username}, id={m['user_id']}) — {state}")

    await message.answer("\n".join(lines))


@router.callback_query(F.data.startswith("intro_done_"))
async def intro_done(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID:
        await callback.answer("Недостаточно прав", show_alert=True)
        return

    user_id = int(callback.data.rsplit("_", 1)[-1])
    await update_intro_status(user_id, "completed")
    await callback.answer("Статус обновлён")
    await callback.message.edit_reply_markup(reply_markup=None)


@router.callback_query(F.data.startswith("intro_toggle_"))
async def intro_toggle(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID:
        await callback.answer("Недостаточно прав", show_alert=True)
        return

    user_id = int(callback.data.rsplit("_", 1)[-1])
    members = await get_intro_members_statuses()
    current = next((m for m in members if int(m["user_id"]) == user_id), None)
    if not current:
        await callback.answer("Пользователь не найден", show_alert=True)
        return

    new_status = "pending" if current.get("intro_status") == "completed" else "completed"
    await update_intro_status(user_id, new_status)
    await callback.answer(f"Статус: {new_status}")


@router.message(Command("help"))
async def cmd_help(message: Message):
    is_admin_or_owner = message.from_user.id in ADMIN_IDS or message.from_user.id == OWNER_ID
    await message.answer(build_help_text(is_admin_or_owner=is_admin_or_owner), parse_mode="HTML")


@router.message(Command("roles"))
@admin_only
async def cmd_roles(message: Message):
    await message.answer(
        "🔐 <b>Роли и доступ</b>\n\n"
        f"👑 Владелец — полный доступ, без лимита.\n"
        f"🛡 Админ — все команды, лимит: {ADMIN_DAILY_COMMAND_LIMIT}/сутки.\n"
        f"🙋 Участник — только пользовательские команды, лимит: {MEMBER_DAILY_COMMAND_LIMIT}/сутки.\n"
        f"🚪 Не участник — только /start, лимит: {OUTSIDER_START_DAILY_LIMIT}/сутки.",
        parse_mode="HTML",
    )


@router.message(Command("usage_stats"))
@admin_only
async def cmd_usage_stats(message: Message):
    rows = await get_command_usage_summary(days=7)
    if not rows:
        await message.answer("📉 Пока нет статистики по использованию команд.")
        return
    lines = ["📊 <b>Среднее использование команд (последние 7 дней)</b>"]
    for row in rows:
        lines.append(
            f"• {row['role']}: всего {row['total_commands']}, "
            f"в среднем {row['avg_per_day']}/день"
        )
    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("health"))
@restricted_command
async def cmd_health(message: Message):
    await message.answer("✅ Бот запущен и отвечает. Используйте /debug_info для подробной диагностики.")


@router.message(Command("status"))
async def cmd_status(message: Message):
    await message.answer("✅ Бот работает. Для списка возможностей используйте /help.")


@router.message(Command("debug_info"))
@restricted_command
async def cmd_debug_info(message: Message):
    from bot.config import ADMIN_IDS
    from bot.utils.topics import get_topics_list_from_db
    import sys

    try:
        me = await message.bot.get_me()
        chat = await message.bot.get_chat(GROUP_ID)
        member = await message.bot.get_chat_member(GROUP_ID, me.id)
        topics = await get_topics_list_from_db()
        is_admin = member.status in ["administrator", "creator"]
        is_forum = getattr(chat, "is_forum", False)

        text = (
            "🔎 <b>Диагностика бота</b>\n\n"
            f"🤖 Бот: @{me.username} (id: <code>{me.id}</code>)\n"
            f"📦 aiogram: <code>{aiogram.__version__}</code>\n"
            f"🐍 Python: <code>{sys.version.split()[0]}</code>\n\n"
            f"👥 Группа: <b>{chat.title}</b> (<code>{chat.id}</code>)\n"
            f"🧵 Форум включён: {'✅' if is_forum else '❌'}\n"
            f"🔐 Права админа у бота: {'✅' if is_admin else '❌'}\n"
            f"📚 Тем в БД: <b>{len(topics)}</b>\n\n"
            f"👤 Ваш id: <code>{message.from_user.id}</code>\n"
            f"🛡 Вы в ADMIN_IDS: {'✅' if message.from_user.id in ADMIN_IDS else '❌'}"
        )
        await message.answer(text, parse_mode="HTML")
    except Exception as e:
        await message.answer(f"❌ Ошибка диагностики: {e}")


@router.message(Command("list_topics"))
@restricted_command
async def list_topics(message: Message):
    from bot.utils.topics import get_topics_list_from_db

    topics = await get_topics_list_from_db()

    if not topics:
        await message.answer(
            "❌ Тем не обнаружено.\n\n"
            "📝 Как добавить темы:\n"
            "1. Откройте группу\n"
            "2. Создайте новую тему\n"
            "3. Отправьте сообщение в эту тему\n"
            "4. Бот автоматически обнаружит тему\n"
            "5. Используйте /list_topics снова"
        )
        return

    response = f"✅ Обнаружено {len(topics)} тем:\n\n"
    for topic in topics:
        response += f"📁 {topic['name']}\n"
        response += f"   ID: {topic['message_thread_id']}\n"

    await message.answer(response)


@router.message(Command("update_topic_names"))
@admin_only
async def update_topic_names(message: Message):
    from bot.database import get_all_topics

    await message.answer("⏳ Обновляю названия тем...")

    try:
        topics = await get_all_topics()
        updated_count = 0

        for topic in topics:
            if topic["name"].startswith("Тема "):
                logger.info("Требуется обновление названия для темы %s", topic["message_thread_id"])
                updated_count += 1

        await message.answer(f"✅ Проверено {len(topics)} тем\nОбновлено: {updated_count}")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


@router.callback_query(F.data == "cancel_create")
async def cancel_create(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.answer("Создание мероприятия отменено", show_alert=True)
