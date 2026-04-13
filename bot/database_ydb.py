# работа с YDB (Managed Service for YDB)

import os
import logging
import ydb
import ydb.aio
from datetime import datetime
from typing import Optional, List, Dict, Any
from aiogram import Bot

logger = logging.getLogger(__name__)

# Конфигурация подключения к YDB
YDB_ENDPOINT = os.getenv("YDB_ENDPOINT", "grpcs://ydb.serverless.yandexcloud.net:2135")
YDB_DATABASE = os.getenv("YDB_DATABASE", "/ru-central1/b1gburmf2sv6jdb39qi4/etnnggcnvg783q3fj957")

# Глобальные переменные для драйвера и пула сессий
_driver = None
_pool = None


async def get_driver():
    """Возвращает инициализированный драйвер YDB."""
    global _driver
    if _driver is None:
        driver_config = ydb.DriverConfig(
            YDB_ENDPOINT,
            YDB_DATABASE,
            credentials=ydb.credentials_from_env_variables(),
            root_certificates=ydb.load_ydb_root_certificate(),
        )
        _driver = ydb.aio.Driver(driver_config)
        try:
            await _driver.wait(timeout=15)
        except TimeoutError:
            logger.error("Connect failed to YDB")
            logger.error("Last reported errors by discovery:")
            logger.error(_driver.discovery_debug_details())
            raise
    return _driver


async def get_pool():
    """Возвращает пул сессий YDB."""
    global _pool
    if _pool is None:
        driver = await get_driver()
        _pool = ydb.aio.SessionPool(driver, size=10)
    return _pool


async def init_db():
    """Создаёт таблицы при первом запуске."""
    pool = await get_pool()
    
    # Создание таблицы users
    await pool.retry_operation(
        lambda session: session.execute_scheme(
            """
            CREATE TABLE IF NOT EXISTS users (
                id Int64 NOT NULL,
                username Utf8,
                notification_settings Utf8 DEFAULT 'all',
                stats_count Int64 DEFAULT 0,
                birth_date Utf8,
                PRIMARY KEY (id)
            )
            """
        )
    )
    
    # Создание таблицы events
    await pool.retry_operation(
        lambda session: session.execute_scheme(
            """
            CREATE TABLE IF NOT EXISTS events (
                id Int64 NOT NULL,
                title Utf8 NOT NULL,
                description Utf8,
                date_time Utf8 NOT NULL,
                duration_minutes Int64,
                location Utf8,
                location_lat Double,
                location_lon Double,
                price_total Double,
                price_per_person Double,
                participant_limit Int64,
                thread_id Int64,
                message_id Int64,
                creator_id Int64,
                weather_info Utf8,
                carpool_enabled Bool DEFAULT false,
                status Utf8 DEFAULT 'active',
                category Utf8,
                created_at Timestamp DEFAULT CurrentUtcTimestamp(),
                PRIMARY KEY (id)
            )
            """
        )
    )
    
    # Создание таблицы participants
    await pool.retry_operation(
        lambda session: session.execute_scheme(
            """
            CREATE TABLE IF NOT EXISTS participants (
                id Int64 NOT NULL,
                event_id Int64 NOT NULL,
                user_id Int64 NOT NULL,
                status Utf8,
                car_seats Int64,
                passenger_of Int64,
                joined_at Timestamp DEFAULT CurrentUtcTimestamp(),
                PRIMARY KEY (id),
                INDEX idx_event_user (event_id, user_id),
                INDEX idx_user (user_id)
            )
            """
        )
    )
    
    # Создание таблицы reviews
    await pool.retry_operation(
        lambda session: session.execute_scheme(
            """
            CREATE TABLE IF NOT EXISTS reviews (
                id Int64 NOT NULL,
                event_id Int64 NOT NULL,
                user_id Int64 NOT NULL,
                rating Int64,
                comment Utf8,
                created_at Timestamp,
                PRIMARY KEY (id),
                INDEX idx_event (event_id),
                INDEX idx_user (user_id)
            )
            """
        )
    )
    
    # Создание таблицы reminder_jobs
    await pool.retry_operation(
        lambda session: session.execute_scheme(
            """
            CREATE TABLE IF NOT EXISTS reminder_jobs (
                id Int64 NOT NULL,
                event_id Int64 NOT NULL,
                interval_seconds Int64,
                scheduled_time Timestamp,
                sent Bool DEFAULT false,
                PRIMARY KEY (id),
                INDEX idx_event (event_id)
            )
            """
        )
    )
    
    # Создание таблицы forum_topics
    await pool.retry_operation(
        lambda session: session.execute_scheme(
            """
            CREATE TABLE IF NOT EXISTS forum_topics (
                id Int64 NOT NULL,
                message_thread_id Int64 NOT NULL,
                name Utf8 NOT NULL,
                is_closed Bool DEFAULT false,
                is_hidden Bool DEFAULT false,
                discovered_at Timestamp DEFAULT CurrentUtcTimestamp(),
                PRIMARY KEY (id),
                UNIQUE INDEX idx_thread_id (message_thread_id)
            )
            """
        )
    )
    
    # Создание таблицы user_category_subscriptions
    await pool.retry_operation(
        lambda session: session.execute_scheme(
            """
            CREATE TABLE IF NOT EXISTS user_category_subscriptions (
                user_id Int64 NOT NULL,
                category Utf8 NOT NULL,
                created_at Timestamp DEFAULT CurrentUtcTimestamp(),
                PRIMARY KEY (user_id, category)
            )
            """
        )
    )
    
    logger.info("Таблицы YDB созданы или уже существуют")


async def get_or_create_user(user_id: int, username: str = None) -> int:
    """Возвращает пользователя из БД, создаёт если нет."""
    pool = await get_pool()
    
    # Проверяем, существует ли пользователь
    result = await pool.retry_operation(
        lambda session: session.transaction().execute(
            """
            SELECT id FROM users WHERE id = $user_id
            """,
            parameters={
                "user_id": user_id,
            },
            commit_tx=True,
        )
    )
    
    if not result[0].rows:
        # Создаем нового пользователя
        await pool.retry_operation(
            lambda session: session.transaction().execute(
                """
                INSERT INTO users (id, username) VALUES ($user_id, $username)
                """,
                parameters={
                    "user_id": user_id,
                    "username": username or "",
                },
                commit_tx=True,
            )
        )
    
    return user_id


async def create_event(event_data: Dict[str, Any]) -> int:
    """Создаёт мероприятие и возвращает его ID."""
    pool = await get_pool()
    
    # Генерируем ID для мероприятия
    # В YDB можно использовать CurrentUtcTimestamp() для генерации уникального ID
    # или использовать sequence, но для простоты будем генерировать на основе времени
    import time
    event_id = int(time.time() * 1000)  # Используем timestamp в миллисекундах
    
    await pool.retry_operation(
        lambda session: session.transaction().execute(
            """
            INSERT INTO events (
                id, title, description, date_time, duration_minutes,
                location, location_lat, location_lon,
                price_total, price_per_person, participant_limit,
                thread_id, message_id, creator_id,
                weather_info, carpool_enabled, category
            ) VALUES (
                $id, $title, $description, $date_time, $duration_minutes,
                $location, $location_lat, $location_lon,
                $price_total, $price_per_person, $participant_limit,
                $thread_id, $message_id, $creator_id,
                $weather_info, $carpool_enabled, $category
            )
            """,
            parameters={
                "id": event_id,
                "title": event_data.get("title", ""),
                "description": event_data.get("description", ""),
                "date_time": event_data.get("date_time", ""),
                "duration_minutes": event_data.get("duration_minutes") or 0,
                "location": event_data.get("location", ""),
                "location_lat": event_data.get("location_lat") or 0.0,
                "location_lon": event_data.get("location_lon") or 0.0,
                "price_total": event_data.get("price_total") or 0.0,
                "price_per_person": event_data.get("price_per_person") or 0.0,
                "participant_limit": event_data.get("participant_limit") or 0,
                "thread_id": event_data.get("thread_id") or 0,
                "message_id": event_data.get("message_id") or 0,
                "creator_id": event_data.get("creator_id", 0),
                "weather_info": event_data.get("weather_info", ""),
                "carpool_enabled": bool(event_data.get("carpool_enabled", False)),
                "category": event_data.get("category", ""),
            },
            commit_tx=True,
        )
    )
    
    return event_id


async def get_event(event_id: int) -> Optional[Dict]:
    """Возвращает мероприятие по ID."""
    pool = await get_pool()
    
    result = await pool.retry_operation(
        lambda session: session.transaction().execute(
            """
            SELECT * FROM events WHERE id = $event_id
            """,
            parameters={
                "event_id": event_id,
            },
            commit_tx=True,
        )
    )
    
    if not result[0].rows:
        return None
    
    row = result[0].rows[0]
    # Преобразуем YDB строку в словарь Python
    event_dict = {}
    for column in row.__fields__:
        value = getattr(row, column)
        # Преобразуем специальные типы YDB
        if hasattr(value, 'isoformat'):
            value = value.isoformat()
        elif isinstance(value, ydb.Decimal):
            value = float(value)
        event_dict[column] = value
    
    return event_dict


async def update_event_message_id(event_id: int, thread_id: int, message_id: int):
    """Сохраняет thread_id и message_id после публикации."""
    pool = await get_pool()
    
    await pool.retry_operation(
        lambda session: session.transaction().execute(
            """
            UPDATE events SET thread_id = $thread_id, message_id = $message_id 
            WHERE id = $event_id
            """,
            parameters={
                "event_id": event_id,
                "thread_id": thread_id or 0,
                "message_id": message_id,
            },
            commit_tx=True,
        )
    )


async def get_active_events() -> List[Dict]:
    """Возвращает все активные мероприятия."""
    pool = await get_pool()
    
    result = await pool.retry_operation(
        lambda session: session.transaction().execute(
            """
            SELECT * FROM events 
            WHERE status = 'active' 
            ORDER BY date_time
            """,
            commit_tx=True,
        )
    )
    
    events = []
    for row in result[0].rows:
        event_dict = {}
        for column in row.__fields__:
            value = getattr(row, column)
            if hasattr(value, 'isoformat'):
                value = value.isoformat()
            elif isinstance(value, ydb.Decimal):
                value = float(value)
            event_dict[column] = value
        events.append(event_dict)
    
    return events


async def add_participant(
    event_id: int,
    user_id: int,
    status: str = "going",
    car_seats: int = None,
    passenger_of: int = None,
) -> bool:
    """Добавляет участника в событие."""
    pool = await get_pool()
    
    # Проверяем, не существует ли уже участник
    result = await pool.retry_operation(
        lambda session: session.transaction().execute(
            """
            SELECT id FROM participants 
            WHERE event_id = $event_id AND user_id = $user_id
            """,
            parameters={
                "event_id": event_id,
                "user_id": user_id,
            },
            commit_tx=True,
        )
    )
    
    if result[0].rows:
        return False
    
    # Генерируем ID для участника
    import time
    participant_id = int(time.time() * 1000) + user_id  # Уникальный ID
    
    await pool.retry_operation(
        lambda session: session.transaction().execute(
            """
            INSERT INTO participants (id, event_id, user_id, status, car_seats, passenger_of)
            VALUES ($id, $event_id, $user_id, $status, $car_seats, $passenger_of)
            """,
            parameters={
                "id": participant_id,
                "event_id": event_id,
                "user_id": user_id,
                "status": status,
                "car_seats": car_seats or 0,
                "passenger_of": passenger_of or 0,
            },
            commit_tx=True,
        )
    )
    
    return True


async def remove_participant(event_id: int, user_id: int):
    """Удаляет участника из события (и пассажиров если водитель)."""
    pool = await get_pool()
    
    # Получаем статус участника
    result = await pool.retry_operation(
        lambda session: session.transaction().execute(
            """
            SELECT status FROM participants 
            WHERE event_id = $event_id AND user_id = $user_id
            """,
            parameters={
                "event_id": event_id,
                "user_id": user_id,
            },
            commit_tx=True,
        )
    )
    
    if result[0].rows:
        status = result[0].rows[0].status
        if status == "driver":
            # Удаляем всех пассажиров этого водителя
            await pool.retry_operation(
                lambda session: session.transaction().execute(
                    """
                    DELETE FROM participants 
                    WHERE event_id = $event_id AND passenger_of = $driver_id
                    """,
                    parameters={
                        "event_id": event_id,
                        "driver_id": user_id,
                    },
                    commit_tx=True,
                )
            )
    
    # Удаляем самого участника
    await pool.retry_operation(
        lambda session: session.transaction().execute(
            """
            DELETE FROM participants 
            WHERE event_id = $event_id AND user_id = $user_id
            """,
            parameters={
                "event_id": event_id,
                "user_id": user_id,
            },
            commit_tx=True,
        )
    )


async def get_participants(event_id: int, status: str = None) -> List[int]:
    """Возвращает список ID участников с указанным статусом."""
    pool = await get_pool()
    
    if status:
        query = """
            SELECT user_id FROM participants 
            WHERE event_id = $event_id AND status = $status
        """
        params = {
            "event_id": event_id,
            "status": status,
        }
    else:
        query = """
            SELECT user_id FROM participants 
            WHERE event_id = $event_id
        """
        params = {
            "event_id": event_id,
        }
    
    result = await pool.retry_operation(
        lambda session: session.transaction().execute(
            query,
            parameters=params,
            commit_tx=True,
        )
    )
    
    return [row.user_id for row in result[0].rows]


async def get_main_participants(event_id: int) -> List[int]:
    """Возвращает ID участников основного состава (идут + карпулинг)."""
    pool = await get_pool()
    
    result = await pool.retry_operation(
        lambda session: session.transaction().execute(
            """
            SELECT DISTINCT user_id FROM participants 
            WHERE event_id = $event_id AND status IN ('going', 'driver', 'passenger')
            """,
            parameters={
                "event_id": event_id,
            },
            commit_tx=True,
        )
    )
    
    return [row.user_id for row in result[0].rows]


async def cancel_event(event_id: int) -> None:
    """Помечает мероприятие как отменённое и очищает участников."""
    pool = await get_pool()
    
    # Помечаем мероприятие как отменённое
    await pool.retry_operation(
        lambda session: session.transaction().execute(
            """
            UPDATE events SET status = 'cancelled' WHERE id = $event_id
            """,
            parameters={
                "event_id": event_id,
            },
            commit_tx=True,
        )
    )
    
    # Удаляем всех участников
    await pool.retry_operation(
        lambda session: session.transaction().execute(
            """
            DELETE FROM participants WHERE event_id = $event_id
            """,
            parameters={
                "event_id": event_id,
            },
            commit_tx=True,
        )
    )


# Остальные функции будут добавлены по мере необходимости
# Для простоты оставим заглушки для остальных функций

async def get_user_stats(user_id: int) -> Dict:
    """⚠️ НОВОЕ: Возвращает статистику пользователя."""
    # Заглушка - нужно реализовать
    return {"events_count": 0, "total_participations": 0}


async def get_top_participants(days: int = 30, limit: int = 3) -> List[Dict]:
    """Топ участников по количеству участий за период."""
    # Заглушка - нужно реализовать
    return []


async def find_events(query: str, period: str = "month", limit: int = 20) -> List[Dict]:
    """Поиск предстоящих активных мероприятий по названию/месту/категории."""
    # Заглушка - нужно реализовать
    return []


async def get_user_events(user_id: int, status: str = None) -> List[Dict]:
    """Возвращает мероприятия пользователя: как участника и/или организатора."""
    # Заглушка - нужно реализовать
    return []


async def move_from_waitlist(event_id: int) -> Optional[int]:
    """Перемещает первого из резерва в основной список."""
    # Заглушка - нужно реализовать
    return None


async def get_drivers_with_passengers(event_id: int) -> List[Dict]:
    """Возвращает список водителей с их пассажирами."""
    # Заглушка - нужно реализовать
    return []


async def get_driver_free_seats(driver_id: int, event_id: int) -> int:
    """Возвращает количество свободных мест у водителя."""
    # Заглушка - нужно реализовать
    return 0


async def add_driver(event_id: int, user_id: int, car_seats: int) -> bool:
    """Добавляет водителя."""
    # Заглушка - нужно реализовать
    return True


async def add_passenger(event_id: int, user_id: int, driver_id: int) -> bool:
    """Добавляет пассажира к водителю."""
    # Заглушка - нужно реализовать
    return True


async def get_forum_topics_raw(bot, chat_id: int):
    """Возвращает список тем форума в виде словарей."""
    # Заглушка - нужно реализовать
    return []


async def update_event_status(event_id: int, status: str):
    """Обновляет статус мероприятия."""
    # Заглушка - нужно реализовать
    pass


async def get_events_for_digest(period: str = "week") -> List[Dict]:
    """Получение предстоящих активных мероприятий для дайджеста."""
    # Заглушка - нужно реализовать
    return []


async def set_user_category_subscriptions(user_id: int, categories: list[str]) -> None:
    """Перезаписывает список подписок пользователя по категориям."""
    pool = await get_pool()
    
    # Удаляем существующие подписки пользователя
    await pool.retry_operation(
        lambda session: session.transaction().execute(
            """
            DELETE FROM user_category_subscriptions WHERE user_id = $user_id
            """,
            parameters={
                "user_id": user_id,
            },
            commit_tx=True,
        )
    )
    
    # Добавляем новые подписки
    for category in categories:
        if category.strip():  # Пропускаем пустые категории
            await pool.retry_operation(
                lambda session: session.transaction().execute(
                    """
                    INSERT INTO user_category_subscriptions (user_id, category)
                    VALUES ($user_id, $category)
                    """,
                    parameters={
                        "user_id": user_id,
                        "category": category.strip(),
                    },
                    commit_tx=True,
                )
            )
    
    logger.info(f"Обновлены подписки пользователя {user_id}: {categories}")


async def get_user_category_subscriptions(user_id: int) -> list[str]:
    """Возвращает категории, на которые подписан пользователь."""
    pool = await get_pool()
    
    result = await pool.retry_operation(
        lambda session: session.transaction().execute(
            """
            SELECT category FROM user_category_subscriptions 
            WHERE user_id = $user_id 
            ORDER BY category
            """,
            parameters={
                "user_id": user_id,
            },
            commit_tx=True,
        )
    )
    
    return [row.category for row in result[0].rows]


async def get_events_for_user_subscriptions(user_id: int, period: str = "week") -> List[Dict]:
    """Возвращает активные события, которые совпадают с подписками пользователя."""
    # Заглушка - нужно реализовать
    return []


async def get_admin_report_metrics() -> Dict[str, Any]:
    """Метрики для /admin_report: активные события, средняя посещаемость, no-show, топ категорий."""
    # Заглушка - нужно реализовать
    return {
        "active_events": 0,
        "avg_attendance": 0,
        "no_show": 0,
        "top_categories": [],
    }


async def save_forum_topic(message_thread_id: int, name: str) -> bool:
    """Сохраняет тему форума в БД."""
    # Заглушка - нужно реализовать
    return True


async def get_all_topics() -> list:
    """Возвращает все известные темы."""
    # Заглушка - нужно реализовать
    return []


async def get_topic_by_id(message_thread_id: int) -> dict:
    """Получает тему по ID."""
    # Заглушка - нужно реализовать
    return None


async def sync_topics_from_config() -> None:
    """Загружает названия тем из topics_config.py в БД."""
    # Заглушка - нужно реализовать
    pass


async def get_topic_name_by_thread_id(thread_id: int | None) -> str | None:
    """Возвращает человекочитаемое название темы."""
    # Заглушка - нужно реализовать
    return None