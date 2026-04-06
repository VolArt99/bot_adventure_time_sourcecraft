# check_env.py - Исправленная версия (без создания бота)
import sys
import aiogram
from aiogram import Bot

print("=" * 60)
print("ПРОВЕРКА ОКРУЖЕНИЯ")
print("=" * 60)
print(f"Python: {sys.executable}")
print(f"Python версия: {sys.version}")
print(f"aiogram версия: {aiogram.__version__}")
print(f"aiogram путь: {aiogram.__file__}")
print("=" * 60)

# ⚠️ ПРОВЕРКА НА КЛАССЕ (без создания инстанса)
has_method = hasattr(Bot, 'get_forum_topics')
print(f"Bot.get_forum_topics доступен: {has_method}")

# Список методов с 'forum'
forum_methods = [m for m in dir(Bot) if 'forum' in m.lower()]
print(f"Методы с 'forum': {forum_methods}")

# Проверка версии
version_parts = aiogram.__version__.split('.')
major = int(version_parts[0])
minor = int(version_parts[1]) if len(version_parts) > 1 else 0

if major >= 3 and minor >= 3:
    print("✅ Версия aiogram поддерживает форум-темы")
else:
    print("⚠️ Требуется aiogram 3.3.0+")

print("=" * 60)
print(f"ИТОГ: get_forum_topics = {'✅ ДОСТУПЕН' if has_method else '❌ НЕ ДОСТУПЕН'}")
print("=" * 60)