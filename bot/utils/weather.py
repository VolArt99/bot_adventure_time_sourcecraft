# получение погоды через OpenWeatherMap

import aiohttp
from config import WEATHER_API_KEY

async def get_weather(city: str = None, lat: float = None, lon: float = None) -> dict:
    """Возвращает словарь с описанием погоды и иконкой."""
    if not WEATHER_API_KEY:
        return {}
    params = {
        "appid": WEATHER_API_KEY,
        "units": "metric",
        "lang": "ru"
    }
    if city:
        params["q"] = city
    elif lat and lon:
        params["lat"] = lat
        params["lon"] = lon
    else:
        return {}
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.openweathermap.org/data/2.5/weather", params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                weather = data["weather"][0]
                temp = data["main"]["temp"]
                icon = weather["icon"]
                description = weather["description"]
                return {
                    "icon": f"https://openweathermap.org/img/wn/{icon}@2x.png",
                    "description": f"{description}, {temp:.0f}°C"
                }
    return {}