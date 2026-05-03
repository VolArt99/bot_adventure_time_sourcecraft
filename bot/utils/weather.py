import aiohttp
import asyncio
import time
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

WEATHER_CACHE_TTL_SECONDS = 300  # 5 minutes
WEATHER_RATE_LIMIT_SECONDS = 2

_weather_session: aiohttp.ClientSession | None = None
_weather_session_lock = asyncio.Lock()
_weather_cache: dict[str, tuple[float, dict]] = {}
_weather_last_request_ts: dict[str, float] = {}
_weather_key_locks: dict[str, asyncio.Lock] = {}


async def _get_weather_session() -> aiohttp.ClientSession:
    global _weather_session
    if _weather_session is not None and not _weather_session.closed:
        return _weather_session

    async with _weather_session_lock:
        if _weather_session is None or _weather_session.closed:
            timeout = aiohttp.ClientTimeout(total=8)
            _weather_session = aiohttp.ClientSession(timeout=timeout)
    return _weather_session


def _cache_key(city: str | None, lat: float | None, lon: float | None) -> str:
    if city:
        return f"city:{city.strip().lower()}"
    if lat is not None and lon is not None:
        return f"coord:{round(lat, 2)}:{round(lon, 2)}"
    return "invalid"


def _is_cache_fresh(cached_at: float) -> bool:
    return time.time() - cached_at < WEATHER_CACHE_TTL_SECONDS


async def get_weather(city: str = None, lat: float = None, lon: float = None) -> dict:
    """Возвращает погоду в удобном для бота формате."""
    if not WEATHER_API_KEY:
        return {}

    key = _cache_key(city, lat, lon)
    if key == "invalid":
        return {}

    cached = _weather_cache.get(key)
    if cached and _is_cache_fresh(cached[0]):
        return cached[1]

    lock = _weather_key_locks.setdefault(key, asyncio.Lock())
    async with lock:
        cached = _weather_cache.get(key)
        if cached and _is_cache_fresh(cached[0]):
            return cached[1]

        now = time.time()
        last_request = _weather_last_request_ts.get(key, 0)
        if now - last_request < WEATHER_RATE_LIMIT_SECONDS and cached:
            return cached[1]

        params = {
            "appid": WEATHER_API_KEY,
            "units": "metric",
            "lang": "ru",
        }
        if city:
            params["q"] = city
        else:
            params["lat"] = lat
            params["lon"] = lon

        try:
            session = await _get_weather_session()
            async with session.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params=params,
            ) as resp:
                _weather_last_request_ts[key] = time.time()
                if resp.status != 200:
                    return cached[1] if cached else {}

                data = await resp.json()
                weather_list = data.get("weather") or []
                main = data.get("main") or {}
                if not weather_list or "temp" not in main:
                    return cached[1] if cached else {}

                weather = weather_list[0]
                result = {
                    "icon": WEATHER_EMOJI.get(weather.get("icon", ""), "🌤"),
                    "description": str(weather.get("description", "")).capitalize(),
                    "temp": round(float(main["temp"])),
                }
                _weather_cache[key] = (time.time(), result)
                return result
        except (aiohttp.ClientError, TimeoutError, ValueError, TypeError):
            return cached[1] if cached else {}
