import aiohttp
from config import WEATHER_API_KEY

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

    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params=params
        ) as resp:
            if resp.status != 200:
                return {}

            data = await resp.json()
            weather = data["weather"][0]
            temp = round(data["main"]["temp"])
            icon_code = weather["icon"]

            return {
                "icon": WEATHER_EMOJI.get(icon_code, "🌤"),
                "description": weather["description"].capitalize(),
                "temp": temp,
            }
