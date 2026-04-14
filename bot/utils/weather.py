import aiohttp
from bot.config import WEATHER_API_KEY

WEATHER_EMOJI = {
    "01d": "☀️", "01n": "🌙",
    "02d": "🌤", "02n": "☁️",
    "03d": "☁️", "03n": "☁️",
    "04d": "☁️", "04n": "☁️",
    "09d": "🌧", "09n": "🌧",
    "10d": "🌦", "10n": "🌧",
    "11d": "⛈", "11n": "⛈",
    "13d": "❄️", "13n": "❄️",
    "50d": "🌫", "50n": "🌫",
}


async def get_weather(city: str = None, lat: float = None, lon: float = None) -> dict:
    """Возвращает погоду в удобном для бота формате."""
    if not WEATHER_API_KEY:
        return {}

    params = {
        "appid": WEATHER_API_KEY,
        "units": "metric",
        "lang": "ru",
    }

    if city:
        params["q"] = city
    elif lat is not None and lon is not None:
        params["lat"] = lat
        params["lon"] = lon
    else:
        return {}

    timeout = aiohttp.ClientTimeout(total=8)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params=params,
            ) as resp:
                if resp.status != 200:
                    return {}

                data = await resp.json()
                weather_list = data.get("weather") or []
                main = data.get("main") or {}
                if not weather_list or "temp" not in main:
                    return {}

                weather = weather_list[0]
                temp = round(float(main["temp"]))
                icon_code = weather.get("icon", "")

                return {
                    "icon": WEATHER_EMOJI.get(icon_code, "🌤"),
                    "description": str(weather.get("description", "")).capitalize(),
                    "temp": temp,
                }
    except (aiohttp.ClientError, TimeoutError, ValueError, TypeError):
        return {}
