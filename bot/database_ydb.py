# работа с YDB (Managed Service for YDB)

import os
import logging
import ydb
import ydb.aio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from aiogram import Bot

logger = logging.getLogger(__name__)

# Конфигурация подключения к YDB
YDB_ENDPOINT = os.getenv("YDB_ENDPOINT")
YDB_DATABASE = os.getenv("YDB_DATABASE")

# Глобальные переменные для драйвера и пула сессий
_driver = None
_pool = None


async def get_driver():
    """Возвращает инициализированный драйвер YDB."""
    global _driver
    if _driver is None:
        if not YDB_ENDPOINT or not YDB_DATABASE:
            raise ValueError("YDB_ENDPOINT и YDB_DATABASE должны быть явно заданы в переменных окружения.")        
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

    await pool.retry_operation(
        lambda session: session.execute_scheme(
            """
            CREATE TABLE IF NOT EXISTS random_meeting_opt_in (
                user_id Int64 NOT NULL,
                is_enabled Bool NOT NULL,
                updated_at Timestamp DEFAULT CurrentUtcTimestamp(),
                PRIMARY KEY (user_id)
            )
            """
        )
    )

    await pool.retry_operation(
        lambda session: session.execute_scheme(
            """
            CREATE TABLE IF NOT EXISTS pending_users (
                user_id Int64 NOT NULL,
                username Utf8,
                full_name Utf8,
                status Utf8,
                created_at Timestamp DEFAULT CurrentUtcTimestamp(),
                PRIMARY KEY (user_id)
            )
            """
        )
    )

    await pool.retry_operation(
        lambda session: session.execute_scheme(
            """
            CREATE TABLE IF NOT EXISTS fsm_states (
                bot_id Int64 NOT NULL,
                chat_id Int64 NOT NULL,
                user_id Int64 NOT NULL,
                thread_id Int64,
                business_connection_id Utf8,
                destiny Utf8 NOT NULL,
                state Utf8,
                data_json Utf8,
                updated_at Timestamp DEFAULT CurrentUtcTimestamp(),
                PRIMARY KEY (bot_id, chat_id, user_id, thread_id, business_connection_id, destiny)
            )
            """
        )
    )
    
    await pool.retry_operation(
        lambda session: session.execute_scheme(
            """
            CREATE TABLE IF NOT EXISTS approved_members (
                user_id Int64 NOT NULL,
                username Utf8,
                full_name Utf8,
                join_date Timestamp DEFAULT CurrentUtcTimestamp(),
                intro_status Utf8 DEFAULT 'pending',
                PRIMARY KEY (user_id)
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


async def add_pending_user(user_id: int, username: str | None, full_name: str | None) -> None:
    pool = await get_pool()
    await pool.retry_operation(
        lambda session: session.transaction().execute(
            """
            UPSERT INTO pending_users (user_id, username, full_name, status)
            VALUES ($user_id, $username, $full_name, $status)
            """,
            parameters={
                "user_id": int(user_id),
                "username": username or "",
                "full_name": full_name or "",
                "status": "waiting_approval",
            },
            commit_tx=True,
        )
    )


async def get_pending_user(user_id: int) -> Optional[Dict[str, Any]]:
    pool = await get_pool()
    result = await pool.retry_operation(
        lambda session: session.transaction().execute(
            """
            SELECT user_id, username, full_name, status, created_at
            FROM pending_users
            WHERE user_id = $user_id
            """,
            parameters={"user_id": int(user_id)},
            commit_tx=True,
        )
    )
    if not result[0].rows:
        return None
    return _normalize_row(result[0].rows[0])


async def delete_pending_user(user_id: int) -> None:
    pool = await get_pool()
    await pool.retry_operation(
        lambda session: session.transaction().execute(
            """
            DELETE FROM pending_users WHERE user_id = $user_id
            """,
            parameters={"user_id": int(user_id)},
            commit_tx=True,
        )
    )


async def is_member_approved(user_id: int) -> bool:
    pool = await get_pool()
    result = await pool.retry_operation(
        lambda session: session.transaction().execute(
            """
            SELECT user_id FROM approved_members WHERE user_id = $user_id
            """,
            parameters={"user_id": int(user_id)},
            commit_tx=True,
        )
    )
    return bool(result[0].rows)


async def approve_pending_user(user_id: int) -> Optional[Dict[str, Any]]:
    pending = await get_pending_user(user_id)
    if not pending:
        return None
    pool = await get_pool()
    await pool.retry_operation(
        lambda session: session.transaction().execute(
            """
            UPSERT INTO approved_members (user_id, username, full_name, intro_status)
            VALUES ($user_id, $username, $full_name, $intro_status)
            """,
            parameters={
                "user_id": int(user_id),
                "username": str(pending.get("username") or ""),
                "full_name": str(pending.get("full_name") or ""),
                "intro_status": "pending",
            },
            commit_tx=True,
        )
    )
    await delete_pending_user(user_id)
    return pending


async def get_pending_intro_members() -> list[Dict[str, Any]]:
    pool = await get_pool()
    result = await pool.retry_operation(
        lambda session: session.transaction().execute(
            """
            SELECT user_id, username, full_name, join_date, intro_status
            FROM approved_members
            WHERE intro_status = 'pending'
            ORDER BY join_date
            """,
            commit_tx=True,
        )
    )
    return [_normalize_row(row) for row in result[0].rows]


async def get_intro_members_statuses() -> list[Dict[str, Any]]:
    pool = await get_pool()
    result = await pool.retry_operation(
        lambda session: session.transaction().execute(
            """
            SELECT user_id, username, full_name, join_date, intro_status
            FROM approved_members
            ORDER BY join_date
            """,
            commit_tx=True,
        )
    )
    return [_normalize_row(row) for row in result[0].rows]


async def update_intro_status(user_id: int, intro_status: str) -> None:
    pool = await get_pool()
    await pool.retry_operation(
        lambda session: session.transaction().execute(
            """
            UPDATE approved_members SET intro_status = $intro_status
            WHERE user_id = $user_id
            """,
            parameters={
                "user_id": int(user_id),
                "intro_status": intro_status,
            },
            commit_tx=True,
        )
    )


async def create_event(event_data: Dict[str, Any]) -> int:
    """Создаёт мероприятие и возвращает его ID."""
    pool = await get_pool()

    # Генерируем ID для мероприятия
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
        if hasattr(value, "isoformat"):
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
            if hasattr(value, "isoformat"):
                value = value.isoformat()
            elif isinstance(value, ydb.Decimal):
                value = float(value)
            event_dict[column] = value
        events.append(event_dict)

    return events


def _normalize_row(row) -> Dict[str, Any]:
    """Преобразует строку YDB в обычный словарь python-типов."""
    event_dict: Dict[str, Any] = {}
    for column in row.__fields__:
        value = getattr(row, column)
        if hasattr(value, "isoformat"):
            value = value.isoformat()
        elif isinstance(value, ydb.Decimal):
            value = float(value)
        event_dict[column] = value
    return event_dict


def _period_to_days(period: str, default_days: int = 7) -> int:
    return {
        "week": 7,
        "month": 30,
        "all": 365 * 10,
    }.get(period, default_days)


def _parse_event_datetime(value: Any) -> Optional[datetime]:
    """Пытается распарсить дату события из строки/объекта datetime."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        normalized = value.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(normalized)
        except ValueError:
            return None
    return None


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


async def get_user_stats(user_id: int) -> Dict:
    """⚠️ НОВОЕ: Возвращает статистику пользователя."""
    pool = await get_pool()

    # Получаем количество мероприятий, где пользователь был организатором
    result_creator = await pool.retry_operation(
        lambda session: session.transaction().execute(
            """
            SELECT COUNT(*) as events_count FROM events 
            WHERE creator_id = $user_id AND status = 'active'
            """,
            parameters={
                "user_id": user_id,
            },
            commit_tx=True,
        )
    )

    events_count = (
        result_creator[0].rows[0].events_count if result_creator[0].rows else 0
    )

    # Получаем общее количество участий
    result_participations = await pool.retry_operation(
        lambda session: session.transaction().execute(
            """
            SELECT COUNT(DISTINCT event_id) as total_participations FROM participants 
            WHERE user_id = $user_id
            """,
            parameters={
                "user_id": user_id,
            },
            commit_tx=True,
        )
    )

    total_participations = (
        result_participations[0].rows[0].total_participations
        if result_participations[0].rows
        else 0
    )

    return {
        "events_count": events_count,
        "total_participations": total_participations,
    }


async def get_top_participants(days: int = 30, limit: int = 3) -> List[Dict]:
    """Топ участников по количеству участий за период."""
    pool = await get_pool()

    # Получаем топ участников за последние N дней
    result = await pool.retry_operation(
        lambda session: session.transaction().execute(
            """
            SELECT 
                p.user_id,
                u.username,
                COUNT(DISTINCT p.event_id) as participation_count
            FROM participants p
            LEFT JOIN users u ON p.user_id = u.id
            WHERE p.joined_at >= CurrentUtcTimestamp() - Interval("PT" || CAST($days AS Utf8) || "H")
            GROUP BY p.user_id, u.username
            ORDER BY participation_count DESC
            LIMIT $limit
            """,
            parameters={
                "days": str(days * 24),  # Конвертируем дни в часы
                "limit": limit,
            },
            commit_tx=True,
        )
    )

    top_participants = []
    for row in result[0].rows:
        top_participants.append(
            {
                "user_id": row.user_id,
                "username": row.username or f"User {row.user_id}",
                "participation_count": row.participation_count,
            }
        )

    return top_participants


async def find_events(query: str, period: str = "month", limit: int = 20) -> List[Dict]:
    """Поиск предстоящих активных мероприятий по названию/месту/категории."""
    pool = await get_pool()

    period_days = _period_to_days(period, default_days=30)
    result = await pool.retry_operation(
        lambda session: session.transaction().execute(
            """
            SELECT * FROM events 
            WHERE status = 'active' 
            AND (
                title LIKE '%' || $query || '%' 
                OR location LIKE '%' || $query || '%'
                OR category LIKE '%' || $query || '%'
                OR description LIKE '%' || $query || '%'
            )
            ORDER BY date_time
            """,
            parameters={
                "query": query,
            },
            commit_tx=True,
        )
    )

    now = datetime.utcnow()
    max_dt = now + timedelta(days=period_days)
    events: List[Dict] = []

    for row in result[0].rows:
        event_dict = _normalize_row(row)
        event_dt = _parse_event_datetime(event_dict.get("date_time"))
        if event_dt is None:
            continue
        if now <= event_dt <= max_dt:
            events.append(event_dict)

    events.sort(key=lambda x: x.get("date_time", ""))
    return events[:limit]


async def get_user_events(user_id: int, status: str = None) -> List[Dict]:
    """Возвращает мероприятия пользователя: как участника и/или организатора."""
    pool = await get_pool()

    if status == "organizer":
        # Мероприятия, где пользователь организатор
        query = """
            SELECT e.* FROM events e
            WHERE e.creator_id = $user_id AND e.status = 'active'
            ORDER BY e.date_time
        """
        params = {"user_id": user_id}
    elif status == "participant":
        # Мероприятия, где пользователь участник
        query = """
            SELECT DISTINCT e.* FROM events e
            JOIN participants p ON e.id = p.event_id
            WHERE p.user_id = $user_id AND e.status = 'active'
            ORDER BY e.date_time
        """
        params = {"user_id": user_id}
    else:
        # Все мероприятия пользователя (и как организатор, и как участник)
        query = """
            SELECT DISTINCT e.* FROM events e
            LEFT JOIN participants p ON e.id = p.event_id AND p.user_id = $user_id
            WHERE (e.creator_id = $user_id OR p.user_id = $user_id) 
            AND e.status = 'active'
            ORDER BY e.date_time
        """
        params = {"user_id": user_id}

    result = await pool.retry_operation(
        lambda session: session.transaction().execute(
            query,
            parameters=params,
            commit_tx=True,
        )
    )

    events = []
    for row in result[0].rows:
        event_dict = {}
        for column in row.__fields__:
            value = getattr(row, column)
            if hasattr(value, "isoformat"):
                value = value.isoformat()
            elif isinstance(value, ydb.Decimal):
                value = float(value)
            event_dict[column] = value
        events.append(event_dict)

    return events


async def move_from_waitlist(event_id: int) -> Optional[int]:
    """Перемещает первого из резерва в основной список."""
    pool = await get_pool()

    event = await get_event(event_id)
    if not event:
        return None

    participant_limit = event.get("participant_limit") or 0
    if participant_limit > 0:
        going = await get_main_participants(event_id)
        if len(going) >= participant_limit:
            return None
        
    # Получаем первого участника из резерва
    result = await pool.retry_operation(
        lambda session: session.transaction().execute(
            """
            SELECT user_id FROM participants 
            WHERE event_id = $event_id AND status = 'waitlist'
            ORDER BY joined_at
            LIMIT 1
            """,
            parameters={
                "event_id": event_id,
            },
            commit_tx=True,
        )
    )

    if not result[0].rows:
        return None

    user_id = result[0].rows[0].user_id

    # Обновляем статус на 'going'
    await pool.retry_operation(
        lambda session: session.transaction().execute(
            """
            UPDATE participants 
            SET status = 'going' 
            WHERE event_id = $event_id AND user_id = $user_id
            """,
            parameters={
                "event_id": event_id,
                "user_id": user_id,
            },
            commit_tx=True,
        )
    )

    return user_id


async def get_drivers_with_passengers(event_id: int) -> List[Dict]:
    """Возвращает список водителей с их пассажирами."""
    pool = await get_pool()

    # Получаем всех водителей
    result_drivers = await pool.retry_operation(
        lambda session: session.transaction().execute(
            """
            SELECT user_id, car_seats FROM participants 
            WHERE event_id = $event_id AND status = 'driver'
            """,
            parameters={
                "event_id": event_id,
            },
            commit_tx=True,
        )
    )

    drivers = []
    for row in result_drivers[0].rows:
        driver_id = row.user_id
        car_seats = row.car_seats

        # Получаем пассажиров этого водителя
        result_passengers = await pool.retry_operation(
            lambda session: session.transaction().execute(
                """
                SELECT user_id FROM participants 
                WHERE event_id = $event_id AND status = 'passenger' AND passenger_of = $driver_id
                """,
                parameters={
                    "event_id": event_id,
                    "driver_id": driver_id,
                },
                commit_tx=True,
            )
        )

        passengers = [
            row_passenger.user_id for row_passenger in result_passengers[0].rows
        ]

        drivers.append(
            {
                "user_id": driver_id,
                "car_seats": car_seats,
                "passengers": passengers,
            }
        )

    return drivers


async def get_driver_free_seats(driver_id: int, event_id: int) -> int:
    """Возвращает количество свободных мест у водителя."""
    pool = await get_pool()

    # Получаем информацию о водителе
    result_driver = await pool.retry_operation(
        lambda session: session.transaction().execute(
            """
            SELECT car_seats FROM participants 
            WHERE event_id = $event_id AND user_id = $driver_id AND status = 'driver'
            """,
            parameters={
                "event_id": event_id,
                "driver_id": driver_id,
            },
            commit_tx=True,
        )
    )

    if not result_driver[0].rows:
        return 0

    car_seats = result_driver[0].rows[0].car_seats

    # Получаем количество пассажиров
    result_passengers = await pool.retry_operation(
        lambda session: session.transaction().execute(
            """
            SELECT COUNT(*) as passenger_count FROM participants 
            WHERE event_id = $event_id AND status = 'passenger' AND passenger_of = $driver_id
            """,
            parameters={
                "event_id": event_id,
                "driver_id": driver_id,
            },
            commit_tx=True,
        )
    )

    passenger_count = (
        result_passengers[0].rows[0].passenger_count if result_passengers[0].rows else 0
    )

    # Свободные места = общие места - пассажиры - 1 (сам водитель)
    free_seats = car_seats - passenger_count - 1
    return max(0, free_seats)


async def add_driver(event_id: int, user_id: int, car_seats: int) -> bool:
    """Добавляет водителя."""
    pool = await get_pool()

    # Проверяем, не является ли уже участником
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

    participant_id = int(time.time() * 1000) + user_id

    await pool.retry_operation(
        lambda session: session.transaction().execute(
            """
            INSERT INTO participants (id, event_id, user_id, status, car_seats)
            VALUES ($id, $event_id, $user_id, 'driver', $car_seats)
            """,
            parameters={
                "id": participant_id,
                "event_id": event_id,
                "user_id": user_id,
                "car_seats": car_seats,
            },
            commit_tx=True,
        )
    )

    return True


async def add_passenger(event_id: int, user_id: int, driver_id: int) -> bool:
    """Добавляет пассажира к водителю."""
    pool = await get_pool()

    # Проверяем, есть ли свободные места у водителя
    free_seats = await get_driver_free_seats(driver_id, event_id)
    if free_seats <= 0:
        return False

    # Проверяем, не является ли уже участником
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

    participant_id = int(time.time() * 1000) + user_id

    await pool.retry_operation(
        lambda session: session.transaction().execute(
            """
            INSERT INTO participants (id, event_id, user_id, status, passenger_of)
            VALUES ($id, $event_id, $user_id, 'passenger', $driver_id)
            """,
            parameters={
                "id": participant_id,
                "event_id": event_id,
                "user_id": user_id,
                "driver_id": driver_id,
            },
            commit_tx=True,
        )
    )

    return True


async def get_forum_topics_raw(bot, chat_id: int):
    """
    Возвращает список тем форума из локального хранилища.

    Telegram Bot API не предоставляет стабильного кросс-версийного метода для
    прямого листинга всех тем, поэтому используем обнаруженные/сохранённые темы.
    """
    try:
        chat = await bot.get_chat(chat_id)

        if not getattr(chat, "is_forum", False):
            return []

        stored_topics = await get_all_topics()
        return [
            {
                "message_thread_id": row.get("message_thread_id"),
                "name": row.get("name", f"Тема {row.get('message_thread_id')}"),
                "is_closed": bool(row.get("is_closed", False)),
                "is_hidden": bool(row.get("is_hidden", False)),
            }
            for row in stored_topics
        ]
    except (TypeError, ValueError) as e:
        logger.error("Ошибка при получении тем форума: %s", e)
        return await get_all_topics()


async def save_forum_topic(message_thread_id: int, name: str) -> bool:
    pool = await get_pool()
    topic_id = int(message_thread_id)

    await pool.retry_operation(
        lambda session: session.transaction().execute(
            """
            UPSERT INTO forum_topics (id, message_thread_id, name, is_closed, is_hidden)
            VALUES ($id, $message_thread_id, $name, false, false)
            """,
            parameters={
                "id": topic_id,
                "message_thread_id": int(message_thread_id),
                "name": name or f"Тема {message_thread_id}",
            },
            commit_tx=True,
        )
    )
    return True


async def get_all_topics() -> List[Dict]:
    pool = await get_pool()
    result = await pool.retry_operation(
        lambda session: session.transaction().execute(
            """
            SELECT message_thread_id, name, is_closed, is_hidden
            FROM forum_topics
            ORDER BY message_thread_id
            """,
            commit_tx=True,
        )
    )
    return [
        {
            "message_thread_id": row.message_thread_id,
            "name": row.name,
            "is_closed": bool(row.is_closed),
            "is_hidden": bool(row.is_hidden),
        }
        for row in result[0].rows
    ]


async def get_topic_by_id(message_thread_id: int) -> Optional[Dict]:
    pool = await get_pool()
    result = await pool.retry_operation(
        lambda session: session.transaction().execute(
            """
            SELECT message_thread_id, name, is_closed, is_hidden
            FROM forum_topics
            WHERE message_thread_id = $message_thread_id
            LIMIT 1
            """,
            parameters={"message_thread_id": int(message_thread_id)},
            commit_tx=True,
        )
    )
    if not result[0].rows:
        return None
    row = result[0].rows[0]
    return {
        "message_thread_id": row.message_thread_id,
        "name": row.name,
        "is_closed": bool(row.is_closed),
        "is_hidden": bool(row.is_hidden),
    }


async def get_topic_name_by_thread_id(message_thread_id: int | None) -> Optional[str]:
    """Возвращает название темы по её thread_id."""
    if message_thread_id in (None, 0):
        return None
    topic = await get_topic_by_id(int(message_thread_id))
    if not topic:
        return None
    return topic.get("name")


async def sync_topics_from_config() -> int:
    try:
        from bot.topics_config import TOPICS_MAPPING
    except Exception:
        return 0

    synced = 0
    for thread_id, name in TOPICS_MAPPING.items():
        await save_forum_topic(int(thread_id), str(name))
        synced += 1
    return synced


async def set_random_meeting_opt_in(user_id: int, is_enabled: bool) -> None:
    pool = await get_pool()
    await pool.retry_operation(
        lambda session: session.transaction().execute(
            """
            UPSERT INTO random_meeting_opt_in (user_id, is_enabled)
            VALUES ($user_id, $is_enabled)
            """,
            parameters={"user_id": int(user_id), "is_enabled": bool(is_enabled)},
            commit_tx=True,
        )
    )


async def get_random_meeting_opt_in_users() -> list[int]:
    pool = await get_pool()
    result = await pool.retry_operation(
        lambda session: session.transaction().execute(
            """
            SELECT user_id FROM random_meeting_opt_in
            WHERE is_enabled = true
            ORDER BY user_id
            """,
            commit_tx=True,
        )
    )
    return [row.user_id for row in result[0].rows]


def build_random_pairs(user_ids: list[int]) -> tuple[list[tuple[int, int]], list[int]]:
    from bot.utils.pairing import build_random_pairs as _build_random_pairs

    return _build_random_pairs(user_ids)


async def update_event_status(event_id: int, status: str):
    """Обновляет статус мероприятия."""
    pool = await get_pool()

    await pool.retry_operation(
        lambda session: session.transaction().execute(
            """
            UPDATE events SET status = $status WHERE id = $event_id
            """,
            parameters={
                "event_id": event_id,
                "status": status,
            },
            commit_tx=True,
        )
    )


async def get_events_for_digest(period: str = "week") -> List[Dict]:
    """Получение предстоящих активных мероприятий для дайджеста."""
    pool = await get_pool()

    period_days = _period_to_days(period)
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

    now = datetime.utcnow()
    max_dt = now + timedelta(days=period_days)
    events: List[Dict] = []
    for row in result[0].rows:
        event_dict = _normalize_row(row)
        event_dt = _parse_event_datetime(event_dict.get("date_time"))
        if event_dt is None:
            continue
        if now <= event_dt <= max_dt:
            events.append(event_dict)

    events.sort(key=lambda x: x.get("date_time", ""))
    return events


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


async def get_events_for_user_subscriptions(
    user_id: int, period: str = "week"
) -> List[Dict]:
    """Возвращает активные события, которые совпадают с подписками пользователя."""
    pool = await get_pool()

    # Получаем подписки пользователя
    subscriptions = await get_user_category_subscriptions(user_id)
    if not subscriptions:
        return []

    period_days = _period_to_days(period)
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

    now = datetime.utcnow()
    max_dt = now + timedelta(days=period_days)
    subscriptions_set = {
        item.strip().lower() for item in subscriptions if item and item.strip()
    }
    events: List[Dict] = []

    for row in result[0].rows:
        event_dict = _normalize_row(row)
        event_category = str(event_dict.get("category") or "").strip().lower()
        if event_category not in subscriptions_set:
            continue
        event_dt = _parse_event_datetime(event_dict.get("date_time"))
        if event_dt is None:
            continue
        if now <= event_dt <= max_dt:
            events.append(event_dict)

    events.sort(key=lambda x: x.get("date_time", ""))
    return events
