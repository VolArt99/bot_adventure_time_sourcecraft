from datetime import datetime
from typing import List, Dict
from html import escape
import pytz
from config import TIMEZONE

TZ = pytz.timezone(TIMEZONE)


def format_duration(minutes: int | None) -> str:
    if not minutes:
        return "не указана"

    hours = minutes // 60
    mins = minutes % 60

    if hours and mins:
        return f"{hours} ч {mins} мин"
    if hours:
        return f"{hours} ч"
    return f"{mins} мин"


def category_to_hashtag(category: str | None) -> str:
    if not category:
        return ""
    safe = category.lower().replace(" ", "_")
    return f"#{safe}"


def category_to_hashtags(categories_raw: str | None) -> str:
    if not categories_raw:
        return "не указана"

    categories = [item.strip() for item in categories_raw.split(",") if item.strip()]
    if not categories:
        return "не указана"
    return " ".join(category_to_hashtag(category) for category in categories)


async def format_event_message(
    event: Dict,
    going_list: List[int],
    waitlist_list: List[int],
    mentions_dict: Dict[int, str],
    topic_name: str | None = None,
    organizer_mention: str | None = None,
) -> str:
    dt = datetime.fromisoformat(event["date_time"]).astimezone(TZ)
    date_str = dt.strftime("%d.%m.%Y")
    time_str = dt.strftime("%H:%M")

    duration = format_duration(event.get("duration_minutes"))

    location = escape(event.get("location") or "не указано")
    title = escape(event["title"])
    description = escape(event.get("description") or "")
    category = escape(category_to_hashtags(event.get("category")))

    price_total = event.get("price_total") or 0
    price_per_person = event.get("price_per_person") or 0
    going_count = len(going_list)
    limit_value = event.get("participant_limit")
    limit_str = str(limit_value) if limit_value else "∞"

    if price_total > 0 and going_count > 0:
        calculated_per_person = round(price_total / going_count, 2)
        price_text = (
            f"💰 Общая: {price_total} ₽\n" f"💰 С человека: {calculated_per_person} ₽"
        )
    elif price_total > 0:
        price_text = f"💰 Общая: {price_total} ₽"
    elif price_per_person > 0:
        price_text = f"💰 С человека: {price_per_person} ₽"
    else:
        price_text = "💰 Бесплатно"

    weather = (
        f"🌤 Погода: {escape(event['weather_info'])}"
        if event.get("weather_info")
        else ""
    )
    carpool = "🚗 Карпулинг включён" if event.get("carpool_enabled") else ""

    going_names = (
        "\n".join(mentions_dict.get(uid, f"id{uid}") for uid in going_list) or "—"
    )
    waitlist_names = (
        "\n".join(mentions_dict.get(uid, f"id{uid}") for uid in waitlist_list) or "—"
    )

    lines = [
        f"📌 <b>{title}</b>",
    ]

    if description:
        lines.append(description)

    if topic_name:
        lines.append(f"🧵 Тема: {escape(topic_name)}")

    if organizer_mention:
        lines.append(f"👤 Организатор: {organizer_mention}")

    if weather:
        lines.append(weather)

    lines.extend(
        [
            f"🗓 {date_str} в {time_str}",
            f"⏱ Длительность: {duration}",
            f"📂 Категория: {category}",
            f"📍 {location}",
            price_text,
            f"👥 Кто уже идёт: {going_count}/{limit_str}",
            "",
            "<b>Список участников:</b>",
            going_names,
            "",
            "<b>Резерв:</b>",
            waitlist_names,
        ]
    )

    if carpool:
        lines.extend(["", carpool])

    if event.get("carpool_enabled"):
        from database import get_drivers_with_passengers

        drivers = await get_drivers_with_passengers(event["id"])
        if drivers:
            lines.extend(["", "<b>🚗 Водители и пассажиры:</b>"])
            for driver in drivers:
                driver_mention = mentions_dict.get(
                    driver["user_id"], f"id{driver['user_id']}"
                )
                free_seats = driver["car_seats"] - len(driver["passengers"])
                lines.append(
                    f"{driver_mention} — мест свободно: {free_seats}/{driver['car_seats']}"
                )
                if driver["passengers"]:
                    passengers = ", ".join(
                        mentions_dict.get(p, f"id{p}") for p in driver["passengers"]
                    )
                    lines.append(f"   Пассажиры: {passengers}")

    return "\n".join(lines)


def format_digest_text(events: List[Dict], usernames_dict: Dict[int, str]) -> str:
    if not events:
        return "📅 На ближайшую неделю мероприятий не запланировано."

    lines = ["<b>📅 Афиша на неделю</b>\n"]
    for e in events:
        dt = datetime.fromisoformat(e["date_time"]).astimezone(TZ)
        date_str = dt.strftime("%d.%m.%Y %H:%M")
        org_name = escape(usernames_dict.get(e["creator_id"], f"id{e['creator_id']}"))
        title = escape(e["title"])
        location = escape(e.get("location") or "не указано")

        lines.append(
            f"<b>🔥 {title}</b>\n"
            f"🗺 Где: {location}\n"
            f"🗓 Когда: {date_str}\n"
            f"👤 Организатор: {org_name}\n"
        )

    return "\n".join(lines)


def format_reminder_text(event: Dict, minutes_until: int) -> str:
    dt = datetime.fromisoformat(event["date_time"]).astimezone(TZ)
    date_str = dt.strftime("%d.%m.%Y %H:%M")
    title = escape(event["title"])
    location = escape(event.get("location") or "не указано")

    return (
        f"🔔 <b>Напоминание о мероприятии</b>\n\n"
        f"📌 {title}\n"
        f"🗓 {date_str}\n"
        f"📍 {location}\n"
        f"⏰ Начинается через {minutes_until} мин"
    )
