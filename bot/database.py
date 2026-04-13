# Адаптер для работы с YDB
# Импортирует все функции из database_ydb.py

from .database_ydb import *

# Переопределяем только те функции, которые нуждаются в изменении
# или добавляем новые функции для обратной совместимости

# Если нужно сохранить обратную совместимость с существующим кодом,
# можно добавить здесь адаптеры для функций, которые изменили сигнатуру

# Например, если в database_ydb.py функция get_event возвращает словарь с другими ключами,
# можно добавить адаптер здесь:

# async def get_event(event_id: int) -> Optional[Dict]:
#     result = await database_ydb.get_event(event_id)
#     if result:
#         # Преобразуем ключи или значения при необходимости
#         result['some_key'] = result.get('some_other_key', default_value)
#     return result

# Но в нашем случае мы импортируем все функции напрямую из database_ydb.py