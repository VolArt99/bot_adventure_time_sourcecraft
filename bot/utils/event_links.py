from __future__ import annotations

from datetime import datetime, timedelta
from urllib.parse import quote_plus


def build_maps_link(location: str | None) -> str | None:
    """Возвращает ссылку Google Maps по текстовому адресу."""
    if not location:
        return None

    cleaned = location.strip()
    if not cleaned:
        return None

    return f"https://www.google.com/maps/search/?api=1&query={quote_plus(cleaned)}"


def build_google_calendar_link(event: dict) -> str | None:
    """Возвращает ссылку на создание события в Google Calendar."""
    if not event:
        return None

    title = (event.get("title") or "Мероприятие").strip()
    date_time_raw = event.get("date_time")
    if not date_time_raw:
        return None

    try:
        start_dt = datetime.fromisoformat(str(date_time_raw))
    except ValueError:
        return None

    duration_minutes = int(event.get("duration_minutes") or 120)
    if duration_minutes <= 0:
        duration_minutes = 120
    end_dt = start_dt + timedelta(minutes=duration_minutes)

    dates = f"{start_dt.strftime('%Y%m%dT%H%M%S')}/{end_dt.strftime('%Y%m%dT%H%M%S')}"
    description = (event.get("description") or "").strip()
    location = (event.get("location") or "").strip()

    params = {
        "action": "TEMPLATE",
        "text": title,
        "dates": dates,
    }
    if description:
        params["details"] = description
    if location:
        params["location"] = location

    query = "&".join(f"{k}={quote_plus(v)}" for k, v in params.items())
    return f"https://calendar.google.com/calendar/render?{query}"


def build_ics_link(event_id: int | str | None) -> str | None:
    """Возвращает deeplink на экспорт ICS через команду бота."""
    if event_id in (None, ""):
        return None

    return f"/ics_{event_id}"