"""Совместимый адаптер импорта функций базы данных.

Поддерживает оба режима запуска:
1) как модуль пакета (python -m bot.main)
2) как скрипт из папки bot (python main.py)
"""

try:
    from .database_ydb import *  # type: ignore[F403]
except ImportError:
    from database_ydb import *  # type: ignore[F403]