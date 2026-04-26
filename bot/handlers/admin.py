from datetime import datetime
from html import escape

from aiogram import Router
from aiogram import F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.config import GROUP_ID, TIMEZONE
from bot.database import (
    get_admin_report_metrics,
    get_events_for_digest,
    get_member_reengage_candidates,
    get_topic_name_by_thread_id,
    get_user_category_subscriptions,
)
from bot.filters.admin import admin_only
from bot.keyboards import broadcast_topics_keyboard, period_keyboard
from bot.utils.helpers import get_user_mention
from bot.utils.topics import get_topics_list_from_db

import pytz

router = Router(name=__name__)
TZ = pytz.timezone(TIMEZONE)


@router.message(Command("admin_report"))
@admin_only
async def cmd_admin_report(message: Message):
    metrics = await get_admin_report_metrics()
    top_categories = metrics["top_categories"]
    if top_categories:
        categories_text = "\n".join(
            f"• {row['category']} — {row['cnt']}" for row in top_categories
        )
    else:
        categories_text = "• пока нет данных"

    text = (
        "📊 <b>Admin Report</b>\n\n"
        f"• Активных событий: <b>{metrics['active_events']}</b>\n"
        f"• Средняя посещаемость: <b>{metrics['avg_attendance']}</b>\n"
        f"• No-show: <b>{metrics['no_show']}</b>\n\n"
        f"<b>Топ категорий:</b>\n{categories_text}"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(Command("send_events_list"))
@admin_only
async def cmd_send_events_list(message: Message):
    await message.answer(
        "Выберите период для публикации списка мероприятий:",
        reply_markup=period_keyboard("broadcast_period"),
    )


@router.callback_query(F.data.startswith("broadcast_period_"))
@admin_only
async def cb_send_events_list_choose_topic(callback: CallbackQuery):
    period = callback.data.removeprefix("broadcast_period_")
    if period not in {"week", "month", "all"}:
        await callback.answer("Некорректный период", show_alert=True)
        return

    topics = await get_topics_list_from_db()
    await callback.message.answer(
        "Выберите группу/подгруппу, куда отправить афишу:",
        reply_markup=broadcast_topics_keyboard(topics, period),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("broadcast_topic_"))
@admin_only
async def cb_send_events_list_publish(callback: CallbackQuery):
    _, _, period, thread_raw = callback.data.split("_", 3)
    thread_id = int(thread_raw) if thread_raw != "0" else None

    text = await _build_events_broadcast_text(period)
    await callback.bot.send_message(
        chat_id=GROUP_ID,
        text=text,
        parse_mode="HTML",
        message_thread_id=thread_id,
        disable_web_page_preview=True,
    )

    topic_name = await get_topic_name_by_thread_id(thread_id)
    target = topic_name or "Основной чат"
    await callback.message.answer(f"✅ Список мероприятий отправлен в: {target}.")
    await callback.answer("Отправлено")


async def _build_events_broadcast_text(period: str) -> str:
    events = await get_events_for_digest(period=period)
    period_title = {"week": "неделю", "month": "месяц", "all": "всё время"}.get(period, "период")
    if not events:
        return f"📭 На ближайшее {period_title} активных мероприятий нет."

    lines = [f"📅 <b>Актуальные мероприятия на {period_title}</b>"]
    for event in events:
        dt = datetime.fromisoformat(event["date_time"]).astimezone(TZ)
        lines.append(
            f"\n• <b>{event['title']}</b>\n"
            f"🗓 {dt.strftime('%d.%m.%Y %H:%M')}\n"
            f"📍 {event.get('location') or 'не указано'}\n"
            f"🆔 <code>{event['id']}</code>"
        )
    return "\n".join(lines)


@router.message(Command("member_reengage"))
@admin_only
async def cmd_member_reengage(message: Message):
    threshold_days = 30
    candidates = await get_member_reengage_candidates(days_inactive=threshold_days)
    if not candidates:
        await message.answer("✅ Нет «молчащих» участников: все были активны в последнее время.")
        return

    lines = [
        f"🤝 <b>Re-engage отчёт</b> (не участвовали ≥ {threshold_days} дней):",
        "Ниже — кого можно мягко позвать на релевантные категории.",
    ]
    for member in candidates[:20]:
        user_id = int(member["user_id"])
        mention = await get_user_mention(user_id, message.bot)
        subs = await get_user_category_subscriptions(user_id)
        relevant = ", ".join(sorted(set(subs))[:3]) if subs else "без подписок"
        safe_relevant = escape(relevant)
        invite_hint = (
            f"Привет! Давно не виделись 🙂 Скоро будет активность по категориям: {relevant}. "
            "Будем рады видеть тебя!"
        )
        lines.append(
            f"\n• {mention} — молчит <b>{member['inactive_days']}</b> дн.\n"
            f"  Релевантно: <i>{safe_relevant}</i>\n"
            f"  Пинг-шаблон: <code>{escape(invite_hint)}</code>"
        )

    await message.answer("\n".join(lines), parse_mode="HTML")