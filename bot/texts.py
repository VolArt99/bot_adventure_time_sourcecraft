# константы текстов сообщений

from datetime import datetime
from typing import List, Dict
import pytz
from config import TIMEZONE
from database import get_drivers_with_passengers

TZ = pytz.timezone(TIMEZONE)

async def format_event_message(event: Dict, going_list: List[int], waitlist_list: List[int], usernames_dict: Dict[int, str]) -> str:
    """Формирует текст сообщения мероприятия (асинхронная)."""
    dt = datetime.fromisoformat(event['date_time']).astimezone(TZ)
    date_str = dt.strftime("%d.%m.%Y")
    time_str = dt.strftime("%H:%M")
    duration = f"{event['duration_minutes']} мин" if event['duration_minutes'] else "не указана"
    location = event['location'] or "не указано"
    price_total = event['price_total'] or 0
    price_per_person = event['price_per_person'] or 0
    limit = event['participant_limit'] or "∞"
    going_count = len(going_list)
    limit_str = str(limit) if limit != "∞" else "∞"
    price_text = ""
    if price_total > 0:
        price_text = f"💰 Общая: {price_total} руб.\n💰 С человека: {price_per_person} руб."
    elif price_per_person > 0:
        price_text = f"💰 С человека: {price_per_person} руб."
    weather = event['weather_info'] or ""
    carpool = "🚗 Карпулинг включён" if event['carpool_enabled'] else ""

    going_names = "\n".join([f"@{usernames_dict.get(uid, str(uid))}" for uid in going_list]) or "—"
    waitlist_names = "\n".join([f"@{usernames_dict.get(uid, str(uid))}" for uid in waitlist_list]) or "—"

    text = (
        f"📌 {event['title']}\n"
        f"{event['description'] or ''}\n"
        f"{weather}\n"
        f"🗓 {date_str} в {time_str}\n"
        f"⏱ Длительность: {duration}\n"
        f"📍 {location}\n"
        f"{price_text}\n"
        f"👥 Участники: {going_count}/{limit_str}\n"
        f"Список:\n{going_names}\n"
        f"Резерв:\n{waitlist_names}\n"
        f"{carpool}"
    )

    # Блок карпулинга
    if event['carpool_enabled']:
        from database import get_drivers_with_passengers
        drivers = await get_drivers_with_passengers(event['id'])
        if drivers:
            text += "\n\n🚗 Карпулинг:\n"
            for driver in drivers:
                driver_username = usernames_dict.get(driver['user_id'], str(driver['user_id']))
                text += f"Водитель: @{driver_username} (мест: {driver['car_seats']})\n"
                if driver['passengers']:
                    passengers = []
                    for p in driver['passengers']:
                        passengers.append(f"@{usernames_dict.get(p, str(p))}")
                    text += "  Пассажиры: " + ", ".join(passengers) + "\n"
                else:
                    text += "  Пассажиры: —\n"
    return text