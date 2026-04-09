from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from database import get_admin_report_metrics
from filters.admin import admin_only

router = Router(name=__name__)


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
