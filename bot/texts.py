# константы текстов сообщений

# ⚠️ ОБНОВЛЕНО: Улучшено форматирование и добавлены новые шаблоны

from datetime import datetime
from typing import List, Dict
import pytz
from config import TIMEZONE

TZ = pytz.timezone(TIMEZONE)

async def format_event_message(event: Dict, going_list: List[int], 
                               waitlist_list: List[int], 
                               usernames_dict: Dict[int, str]) -> str:
    """Формирует текст сообщения мероприятия."""
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
    
    # ⚠️ ОБНОВЛЕНО: Авто-расчёт стоимости с человека
    if price_total > 0 and going_count > 0:
        calculated_per_person = round(price_total / going_count, 2)
        price_text = f"💰 Общая: {price_total} руб.\n💰 С человека: {calculated_per_person} руб."
    elif price_per_person > 0:
        price_text = f"💰 С человека: {price_per_person} руб."
    else:
        price_text = "💰 Бесплатно"
    
    weather = f"🌤 {event['weather_info']}" if event.get('weather_info') else ""
    carpool = "🚗 Карпулинг включён" if event.get('carpool_enabled') else ""
    
    going_names = "\n".join([f"@{usernames_dict.get(uid, str(uid))}" for uid in going_list]) or "—"
    waitlist_names = "\n".join([f"@{usernames_dict.get(uid, str(uid))}" for uid in waitlist_list]) or "—"
    
    text = (
        f"📌 **{event['title']}**\n"
        f"{event.get('description') or ''}\n"
        f"{weather}\n"
        f"🗓 {date_str} в {time_str}\n"
        f"⏱ Длительность: {duration}\n"
        f"📍 {location}\n"
        f"{price_text}\n"
        f"👥 Участники: {going_count}/{limit_str}\n\n"
        f"**Список:**\n{going_names}\n\n"
        f"**Резерв:**\n{waitlist_names}\n"
        f"{carpool}"
    )
    
    # Блок карпулинга
    if event.get('carpool_enabled'):
        from database import get_drivers_with_passengers
        drivers = await get_drivers_with_passengers(event['id'])
        if drivers:
            text += "\n\n**🚗 Карпулинг:**\n"
            for driver in drivers:
                driver_username = usernames_dict.get(driver['user_id'], str(driver['user_id']))
                free_seats = driver['car_seats'] - len(driver['passengers'])
                text += f"Водитель: @{driver_username} (свободно: {free_seats}/{driver['car_seats']})\n"
                if driver['passengers']:
                    passengers = ", ".join([f"@{usernames_dict.get(p, str(p))}" for p in driver['passengers']])
                    text += f"  Пассажиры: {passengers}\n"
    
    return text

# ⚠️ НОВОЕ: Шаблон дайджеста
def format_digest_text(events: List[Dict], usernames_dict: Dict[int, str]) -> str:
    """Формирует текст дайджеста."""
    if not events:
        return "📅 На ближайшую неделю мероприятий не запланировано."
    
    lines = ["**📅 Афиша на неделю**\n"]
    for e in events:
        dt = datetime.fromisoformat(e['date_time']).astimezone(TZ)
        date_str = dt.strftime("%d.%m.%Y %H:%M")
        org_name = usernames_dict.get(e['creator_id'], f"id{e['creator_id']}")
        lines.append(
            f"**🔥 {e['title']}**\n"
            f"🗺 Где: {e['location'] or 'не указано'}\n"
            f"🗓 Когда: {date_str}\n"
            f"👤 Организатор: @{org_name}\n"
            f"⛓ Подробнее в ветке мероприятия\n\n"
        )
    return "\n".join(lines)

# ⚠️ НОВОЕ: Шаблон напоминания
def format_reminder_text(event: Dict, minutes_until: int) -> str:
    """Формирует текст напоминания."""
    dt = datetime.fromisoformat(event['date_time']).astimezone(TZ)
    date_str = dt.strftime("%d.%m.%Y %H:%M")
    return (
        f"🔔 **Напоминание о мероприятии**\n\n"
        f"📌 {event['title']}\n"
        f"🗓 {date_str}\n"
        f"📍 {event['location'] or 'не указано'}\n"
        f"⏰ Начинается через {minutes_until} мин\n\n"
        f"Не опаздывайте! 🎉"
    )