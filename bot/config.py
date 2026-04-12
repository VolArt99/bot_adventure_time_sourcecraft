 # загрузка настроек из .env

# ⚠️ ОБНОВЛЕНО: Добавлена валидация и дефолтные значения

import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
BOT_PROXY_URL = os.getenv("BOT_PROXY_URL", "").strip() or None

# ⚠️ ВАЖНО: GROUP_ID должен быть числом (например, -1001234567890)
# Для получения ID группы отправьте боту команду /test_chat
GROUP_ID = int(os.getenv("GROUP_ID")) if os.getenv("GROUP_ID") else 0

# ⚠️ ОБНОВЛЕНО: ADMIN_IDS теперь список организаторов (не только админы)
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []

# ⚠️ ОБНОВЛЕНО: Часовой пояс для Санкт-Петербурга
TIMEZONE = os.getenv("TIMEZONE", "Europe/Moscow")  # Москва = СПб

# Настройки напоминаний (в секундах)
REMINDER_INTERVALS = [86400, 10800, 7200, 3600, 1800]  # 1 день, 3ч, 2ч, 1ч, 30мин

# Настройки дайджеста
DIGEST_DAY_OF_WEEK = 1  # Понедельник (0=Пн, 6=Вс)
DIGEST_HOUR = 10  # 10:00