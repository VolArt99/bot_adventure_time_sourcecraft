 # загрузка настроек из .env

import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не установлен. Убедитесь, что переменная окружения BOT_TOKEN установлена.")

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# ⚠️ ВАЖНО: GROUP_ID должен быть числом (например, -1001234567890)
# Для получения ID группы отправьте боту команду /test_chat
GROUP_ID = int(os.getenv("GROUP_ID")) if os.getenv("GROUP_ID") else 0

# ⚠️ ОБНОВЛЕНО: ADMIN_IDS теперь список организаторов (не только админы)
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []
OWNER_ID = int(os.getenv("OWNER_ID")) if os.getenv("OWNER_ID") else 0
OUTSIDER_ALLOWED_COMMANDS = {
    cmd.strip().lower()
    for cmd in os.getenv("OUTSIDER_ALLOWED_COMMANDS", "start,help,status").split(",")
    if cmd.strip()
}

# Дневные лимиты по отправке команд
ADMIN_DAILY_COMMAND_LIMIT = int(os.getenv("ADMIN_DAILY_COMMAND_LIMIT", "150"))
MEMBER_DAILY_COMMAND_LIMIT = int(os.getenv("MEMBER_DAILY_COMMAND_LIMIT", "60"))
OUTSIDER_START_DAILY_LIMIT = int(os.getenv("OUTSIDER_START_DAILY_LIMIT", "5"))

# Команды, доступные участнику группы
MEMBER_ALLOWED_COMMANDS = {
    cmd.strip().lower()
    for cmd in os.getenv(
        "MEMBER_ALLOWED_COMMANDS",
        "start,help,my_events,digest,subscriptions,my_digest,my_stats,top,find_events,random_optin,random_optout,"
        "set_responsible,add_participant_manual,set_carpool_manual,add_passenger_manual",
    ).split(",")
    if cmd.strip()
}

# Команды, которые могут выполнять только админы (ADMIN_IDS).
# Нужны для ограничения сервисных операций обычным участникам.
RESTRICTED_COMMANDS = {
    cmd.strip().lower()
    for cmd in os.getenv(
        "RESTRICTED_COMMANDS",
        "debug_info,list_topics,update_topic_names,admin_report,random_pairs",
    ).split(",")
    if cmd.strip()
}

# ⚠️ ОБНОВЛЕНО: Часовой пояс для Санкт-Петербурга
TIMEZONE = os.getenv("TIMEZONE", "Europe/Moscow")  # Москва = СПб

# Настройки напоминаний (в секундах)
REMINDER_INTERVALS = [86400, 10800, 7200, 3600, 1800]  # 1 день, 3ч, 2ч, 1ч, 30мин

# Настройки дайджеста
DIGEST_DAY_OF_WEEK = int(os.getenv("DIGEST_DAY_OF_WEEK", "1"))  # Понедельник (1=Пн, 7=Вс)
DIGEST_HOUR = int(os.getenv("DIGEST_HOUR", "10"))  # 10:00
if not 1 <= DIGEST_DAY_OF_WEEK <= 7:
    raise ValueError("DIGEST_DAY_OF_WEEK должен быть в диапазоне 1..7 (1=Пн, 7=Вс).")
if not 0 <= DIGEST_HOUR <= 23:
    raise ValueError("DIGEST_HOUR должен быть в диапазоне 0..23.")