 # загрузка настроек из .env

import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
GROUP_ID = int(os.getenv("GROUP_ID"))
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []
TIMEZONE = os.getenv("TIMEZONE", "Europe/Moscow")