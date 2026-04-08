# работа с БД (aiosqlite, создание таблиц, CRUD)

# ⚠️ ОБНОВЛЕНО: Добавлены новые функции и улучшена обработка ошибок

import aiosqlite
from datetime import datetime
from typing import Optional, List, Dict, Any
from aiogram import Bot

DB_PATH = "data/events.db"


async def init_db():
    """Создаёт таблицы при первом запуске."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            notification_settings TEXT DEFAULT 'all',
            stats_count INTEGER DEFAULT 0,
            birth_date TEXT
        )
        """
        )
        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            date_time TEXT NOT NULL,
            duration_minutes INTEGER,
            location TEXT,
            location_lat REAL,
            location_lon REAL,
            price_total REAL,
            price_per_person REAL,
            participant_limit INTEGER,
            thread_id INTEGER,
            message_id INTEGER,
            creator_id INTEGER,
            weather_info TEXT,
            carpool_enabled INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active',
            category TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(creator_id) REFERENCES users(id)
        )
        """
        )
        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER,
            user_id INTEGER,
            status TEXT,
            car_seats INTEGER,
            passenger_of INTEGER,
            joined_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(event_id) REFERENCES events(id),
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(passenger_of) REFERENCES users(id)
        )
        """
        )
        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER,
            user_id INTEGER,
            rating INTEGER,
            comment TEXT,
            created_at TEXT,
            FOREIGN KEY(event_id) REFERENCES events(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
        )
        # ⚠️ НОВОЕ: Таблица для напоминаний
        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS reminder_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER,
            interval_seconds INTEGER,
            scheduled_time TEXT,
            sent INTEGER DEFAULT 0
        )
        """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS forum_topics (
                id INTEGER PRIMARY KEY,
                message_thread_id INTEGER UNIQUE,
                name TEXT NOT NULL,
                is_closed INTEGER DEFAULT 0,
                is_hidden INTEGER DEFAULT 0,
                discovered_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        await db.commit()


# ----- Функции для пользователей -----
async def get_or_create_user(user_id: int, username: str = None):
    """Возвращает пользователя из БД, создаёт если нет."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id FROM users WHERE id = ?", (user_id,)
        ) as cursor:
            if await cursor.fetchone() is None:
                await db.execute(
                    "INSERT INTO users (id, username) VALUES (?, ?)",
                    (user_id, username),
                )
                await db.commit()
        return user_id


async def get_user_stats(user_id: int) -> Dict:
    """⚠️ НОВОЕ: Возвращает статистику пользователя."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT 
                COUNT(DISTINCT event_id) as events_count,
                SUM(CASE WHEN status = 'going' THEN 1 ELSE 0 END) as total_participations
            FROM participants WHERE user_id = ?
        """,
            (user_id,),
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else {"events_count": 0, "total_participations": 0}


async def get_top_participants(days: int = 30, limit: int = 3) -> List[Dict]:
    """Топ участников по количеству участий за период."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT p.user_id, COUNT(*) as participations
            FROM participants p
            JOIN events e ON e.id = p.event_id
            WHERE p.status IN ('going', 'driver', 'passenger')
              AND e.date_time >= datetime('now', ?)
            GROUP BY p.user_id
            ORDER BY participations DESC, p.user_id ASC
            LIMIT ?
            """,
            (f"-{days} days", limit),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def find_events(query: str, period: str = "month", limit: int = 20) -> List[Dict]:
    """Поиск предстоящих активных мероприятий по названию/месту/категории."""
    from datetime import datetime, timedelta

    normalized = f"%{query.strip().lower()}%"
    now = datetime.now()

    if period == "week":
        end = now + timedelta(days=7)
    elif period == "month":
        end = now + timedelta(days=30)
    else:
        end = None

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if end is None:
            sql = """
                SELECT * FROM events
                WHERE status = 'active'
                  AND date_time >= ?
                  AND (
                    lower(title) LIKE ?
                    OR lower(COALESCE(location, '')) LIKE ?
                    OR lower(COALESCE(category, '')) LIKE ?
                  )
                ORDER BY date_time ASC
                LIMIT ?
            """
            params = (now.isoformat(), normalized, normalized, normalized, limit)
        else:
            sql = """
                SELECT * FROM events
                WHERE status = 'active'
                  AND date_time BETWEEN ? AND ?
                  AND (
                    lower(title) LIKE ?
                    OR lower(COALESCE(location, '')) LIKE ?
                    OR lower(COALESCE(category, '')) LIKE ?
                  )
                ORDER BY date_time ASC
                LIMIT ?
            """
            params = (
                now.isoformat(),
                end.isoformat(),
                normalized,
                normalized,
                normalized,
                limit,
            )

        async with db.execute(sql, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        
        
# ----- Функции для мероприятий -----
async def create_event(event_data: Dict[str, Any]) -> int:
    """Создаёт мероприятие и возвращает его ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
        INSERT INTO events (
            title, description, date_time, duration_minutes,
            location, location_lat, location_lon,
            price_total, price_per_person, participant_limit,
            thread_id, message_id, creator_id,
            weather_info, carpool_enabled, category
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                event_data["title"],
                event_data.get("description"),
                event_data["date_time"],
                event_data.get("duration_minutes"),
                event_data.get("location"),
                event_data.get("location_lat"),
                event_data.get("location_lon"),
                event_data.get("price_total"),
                event_data.get("price_per_person"),
                event_data.get("participant_limit"),
                event_data.get("thread_id"),
                event_data.get("message_id"),
                event_data.get("creator_id"),
                event_data.get("weather_info"),
                1 if event_data.get("carpool_enabled") else 0,
                event_data.get("category"),
            ),
        )
        await db.commit()
        return cursor.lastrowid


async def get_event(event_id: int) -> Optional[Dict]:
    """Возвращает мероприятие по ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM events WHERE id = ?", (event_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def update_event_message_id(event_id: int, thread_id: int, message_id: int):
    """Сохраняет thread_id и message_id после публикации."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE events SET thread_id = ?, message_id = ? WHERE id = ?",
            (thread_id, message_id, event_id),
        )
        await db.commit()


async def get_active_events() -> List[Dict]:
    """Возвращает все активные мероприятия."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM events WHERE status = 'active' ORDER BY date_time ASC"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


# ⚠️ НОВОЕ: Получение мероприятий пользователя
async def get_user_events(user_id: int, status: str = None) -> List[Dict]:
    """Возвращает мероприятия пользователя: как участника и/или организатора."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = """
        SELECT DISTINCT e.*
        FROM events e
        LEFT JOIN participants p ON e.id = p.event_id
        WHERE p.user_id = ? OR e.creator_id = ?
        """
        params = [user_id, user_id]
        if status:
            query += " AND e.status = ?"
            params.append(status)
        query += " ORDER BY e.date_time ASC"
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


# ----- Функции для участников -----
async def add_participant(
    event_id: int,
    user_id: int,
    status: str = "going",
    car_seats: int = None,
    passenger_of: int = None,
) -> bool:
    """Добавляет участника в событие."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id FROM participants WHERE event_id = ? AND user_id = ?",
            (event_id, user_id),
        ) as cursor:
            if await cursor.fetchone():
                return False
        await db.execute(
            """
        INSERT INTO participants (event_id, user_id, status, car_seats, passenger_of)
        VALUES (?, ?, ?, ?, ?)
        """,
            (event_id, user_id, status, car_seats, passenger_of),
        )
        await db.commit()
        return True


async def remove_participant(event_id: int, user_id: int):
    """Удаляет участника из события (и пассажиров если водитель)."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT status FROM participants WHERE event_id = ? AND user_id = ?",
            (event_id, user_id),
        ) as cursor:
            row = await cursor.fetchone()
            if row and row[0] == "driver":
                await db.execute(
                    "DELETE FROM participants WHERE event_id = ? AND passenger_of = ?",
                    (event_id, user_id),
                )
        await db.execute(
            "DELETE FROM participants WHERE event_id = ? AND user_id = ?",
            (event_id, user_id),
        )
        await db.commit()


async def get_participants(event_id: int, status: str = None) -> List[int]:
    """Возвращает список ID участников с указанным статусом."""
    query = "SELECT user_id FROM participants WHERE event_id = ?"
    params = [event_id]
    if status:
        query += " AND status = ?"
        params.append(status)
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]


async def get_main_participants(event_id: int) -> List[int]:
    """Возвращает ID участников основного состава (идут + карпулинг)."""
    statuses = ("going", "driver", "passenger")
    placeholders = ",".join("?" for _ in statuses)
    query = (
        f"SELECT DISTINCT user_id FROM participants "
        f"WHERE event_id = ? AND status IN ({placeholders})"
    )
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(query, (event_id, *statuses)) as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]


async def move_from_waitlist(event_id: int) -> Optional[int]:
    """Перемещает первого из резерва в основной список."""
    event = await get_event(event_id)
    if not event or event["status"] != "active":
        return None
    going = await get_participants(event_id, "going")
    if event["participant_limit"] and len(going) >= event["participant_limit"]:
        return None
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """
            SELECT user_id FROM participants 
            WHERE event_id = ? AND status = 'waitlist' 
            ORDER BY id ASC LIMIT 1
        """,
            (event_id,),
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                user_id = row[0]
                await db.execute(
                    """
                    UPDATE participants SET status = 'going' 
                    WHERE event_id = ? AND user_id = ?
                """,
                    (event_id, user_id),
                )
                await db.commit()
                return user_id
    return None


# ----- Функции для карпулинга -----
async def get_drivers_with_passengers(event_id: int) -> List[Dict]:
    """Возвращает список водителей с их пассажирами."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT user_id, car_seats FROM participants 
            WHERE event_id = ? AND status = 'driver'
        """,
            (event_id,),
        ) as cursor:
            drivers = await cursor.fetchall()
        result = []
        for driver in drivers:
            driver_id = driver["user_id"]
            async with db.execute(
                """
                SELECT user_id FROM participants 
                WHERE event_id = ? AND status = 'passenger' AND passenger_of = ?
            """,
                (event_id, driver_id),
            ) as cur:
                passengers = await cur.fetchall()
            result.append(
                {
                    "user_id": driver_id,
                    "car_seats": driver["car_seats"],
                    "passengers": [p["user_id"] for p in passengers],
                }
            )
        return result


async def get_driver_free_seats(driver_id: int, event_id: int) -> int:
    """Возвращает количество свободных мест у водителя."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """
            SELECT car_seats FROM participants 
            WHERE event_id = ? AND user_id = ? AND status = 'driver'
        """,
            (event_id, driver_id),
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return 0
            total_seats = row[0]
        async with db.execute(
            """
            SELECT COUNT(*) FROM participants 
            WHERE event_id = ? AND status = 'passenger' AND passenger_of = ?
        """,
            (event_id, driver_id),
        ) as cursor:
            occupied = (await cursor.fetchone())[0]
        return total_seats - occupied


async def add_driver(event_id: int, user_id: int, car_seats: int) -> bool:
    """Добавляет водителя."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """
            SELECT status FROM participants 
            WHERE event_id = ? AND user_id = ?
        """,
            (event_id, user_id),
        ) as cursor:
            existing = await cursor.fetchone()
            if existing:
                status = existing[0]
                if status in ("going", "waitlist"):
                    await db.execute(
                        """
                        UPDATE participants SET status = 'driver', car_seats = ? 
                        WHERE event_id = ? AND user_id = ?
                    """,
                        (car_seats, event_id, user_id),
                    )
                else:
                    return False
            else:
                await db.execute(
                    """
                    INSERT INTO participants (event_id, user_id, status, car_seats) 
                    VALUES (?, ?, 'driver', ?)
                """,
                    (event_id, user_id, car_seats),
                )
        await db.commit()
        return True


async def add_passenger(event_id: int, user_id: int, driver_id: int) -> bool:
    """Добавляет пассажира к водителю."""
    free_seats = await get_driver_free_seats(driver_id, event_id)
    if free_seats <= 0:
        return False
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """
            SELECT status FROM participants 
            WHERE event_id = ? AND user_id = ?
        """,
            (event_id, user_id),
        ) as cursor:
            existing = await cursor.fetchone()
            if existing:
                status = existing[0]
                if status in ("going", "waitlist"):
                    await db.execute(
                        """
                        UPDATE participants SET status = 'passenger', passenger_of = ? 
                        WHERE event_id = ? AND user_id = ?
                    """,
                        (driver_id, event_id, user_id),
                    )
                else:
                    return False
            else:
                await db.execute(
                    """
                    INSERT INTO participants (event_id, user_id, status, passenger_of) 
                    VALUES (?, ?, 'passenger', ?)
                """,
                    (event_id, user_id, driver_id),
                )
        await db.commit()
        return True


# ✅ ИЗМЕНЕНИЕ: Функция get_forum_topics() - возвращаем правильный формат
async def get_forum_topics_raw(bot, chat_id: int):
    """Возвращает список тем форума в виде словарей."""
    try:
        response = await bot.get_forum_topics(chat_id)
        # response может быть ForumTopicUpdated объект или список
        if hasattr(response, "topics"):
            return response.topics  # Если объект
        return response or []  # Если список
    except Exception as e:
        print(f"Ошибка при получении тем: {e}")
        return []


# ----- Вспомогательные функции -----
async def update_event_status(event_id: int, status: str):
    """Обновляет статус мероприятия."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE events SET status = ? WHERE id = ?", (status, event_id)
        )
        await db.commit()


async def cancel_event(event_id: int) -> None:
    """Помечает мероприятие как отменённое и очищает участников."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE events SET status = 'cancelled' WHERE id = ?", (event_id,))
        await db.execute("DELETE FROM participants WHERE event_id = ?", (event_id,))
        await db.commit()
        

async def get_events_for_digest(period: str = "week") -> List[Dict]:
    """Получение предстоящих активных мероприятий для дайджеста."""
    from datetime import datetime, timedelta

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        now = datetime.now().isoformat()

        if period == "week":
            end = (datetime.now() + timedelta(days=7)).isoformat()
            query = """
                SELECT * FROM events
                WHERE status = 'active' AND date_time BETWEEN ? AND ?
                ORDER BY date_time ASC
            """
            params = (now, end)
        elif period == "month":
            end = (datetime.now() + timedelta(days=30)).isoformat()
            query = """
                SELECT * FROM events
                WHERE status = 'active' AND date_time BETWEEN ? AND ?
                ORDER BY date_time ASC
            """
            params = (now, end)
        else:
            query = """
                SELECT * FROM events
                WHERE status = 'active' AND date_time >= ?
                ORDER BY date_time ASC
            """
            params = (now,)

        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def save_forum_topic(message_thread_id: int, name: str) -> bool:
    """Сохраняет тему форума в БД."""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT OR REPLACE INTO forum_topics (message_thread_id, name) VALUES (?, ?)",
                (message_thread_id, name),
            )
            await db.commit()
        return True
    except Exception as e:
        print(f"Ошибка сохранения темы: {e}")
        return False


async def get_all_topics() -> list:
    """Возвращает все известные темы."""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM forum_topics ORDER BY name") as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    except Exception as e:
        print(f"Ошибка получения тем: {e}")
        return []


async def get_topic_by_id(message_thread_id: int) -> dict:
    """Получает тему по ID."""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM forum_topics WHERE message_thread_id = ?",
                (message_thread_id,),
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    except Exception as e:
        print(f"Ошибка получения темы: {e}")
        return None


async def sync_topics_from_config() -> None:
    """Загружает названия тем из topics_config.py в БД."""
    try:
        from topics_config import TOPICS_MAPPING
    except ImportError:
        return

    if not TOPICS_MAPPING:
        return

    async with aiosqlite.connect(DB_PATH) as db:
        for thread_id, name in TOPICS_MAPPING.items():
            await db.execute(
                """
                INSERT INTO forum_topics (message_thread_id, name)
                VALUES (?, ?)
                ON CONFLICT(message_thread_id) DO UPDATE SET
                    name = excluded.name
                """,
                (thread_id, name),
            )
        await db.commit()


async def get_topic_name_by_thread_id(thread_id: int | None) -> str | None:
    """Возвращает человекочитаемое название темы."""
    if thread_id is None:
        return None

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT name FROM forum_topics WHERE message_thread_id = ?",
            (thread_id,),
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None
