import sys
import aiogram

print("=" * 60)
print("ПРОВЕРКА ОКРУЖЕНИЯ")
print("=" * 60)
print(f"Python: {sys.executable}")
print(f"Python версия: {sys.version}")
print(f"aiogram версия: {aiogram.__version__}")
print(f"aiogram путь: {aiogram.__file__}")
print("=" * 60)

print("ℹ️ Telegram Bot API не предоставляет универсального способа получить все ID тем напрямую.")
print("ℹ️ Бот использует локально обнаруженные темы (из входящих сообщений) и topics_config.py.")

# Проверка версии
version_parts = aiogram.__version__.split('.')
major = int(version_parts[0])
minor = int(version_parts[1]) if len(version_parts) > 1 else 0

if major >= 3 and minor >= 3:
    print("✅ Версия aiogram поддерживает форум-темы")
else:
    print("⚠️ Требуется aiogram 3.3.0+")

print("=" * 60)
print("ИТОГ: ориентируйтесь на /list_topics и таблицу forum_topics в БД.")
print("=" * 60)