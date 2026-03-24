# работа с БД (aiosqlite, создание таблиц, CRUD)

import aiosqlite
from datetime import datetime
from typing import Optional, List, Dict, Any

DB_PATH = "data/events.db"

async def init_db():
    """Создаёт таблицы при первом запуске."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                notification_settings TEXT DEFAULT 'all',
                stats_count INTEGER DEFAULT 0,
                birth_date TEXT
            )
        """)
        await db.execute("""
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
                limit INTEGER,
                thread_id INTEGER,
                message_id INTEGER,
                creator_id INTEGER,
                weather_info TEXT,
                carpool_enabled INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                category TEXT,
                FOREIGN KEY(creator_id) REFERENCES users(id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER,
                user_id INTEGER,
                status TEXT,  -- going, waitlist, driver, passenger
                car_seats INTEGER,
                passenger_of INTEGER,
                FOREIGN KEY(event_id) REFERENCES events(id),
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(passenger_of) REFERENCES users(id)
            )
        """)
        await db.execute("""
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
        """)
        await db.commit()

# ----- Функции для работы с пользователями -----
async def get_or_create_user(user_id: int, username: str = None):
    """Возвращает пользователя из БД, создаёт если нет."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id FROM users WHERE id = ?", (user_id,)) as cursor:
            if await cursor.fetchone() is None:
                await db.execute("INSERT INTO users (id, username) VALUES (?, ?)", (user_id, username))
                await db.commit()
    return user_id

# ----- Функции для мероприятий -----
async def create_event(event_data: Dict[str, Any]) -> int:
    """Создаёт мероприятие и возвращает его ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO events (
                title, description, date_time, duration_minutes,
                location, location_lat, location_lon,
                price_total, price_per_person, limit,
                thread_id, message_id, creator_id,
                weather_info, carpool_enabled, category
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event_data['title'], event_data.get('description'),
            event_data['date_time'], event_data.get('duration_minutes'),
            event_data.get('location'), event_data.get('location_lat'),
            event_data.get('location_lon'), event_data.get('price_total'),
            event_data.get('price_per_person'), event_data.get('limit'),
            event_data.get('thread_id'), event_data.get('message_id'),
            event_data.get('creator_id'), event_data.get('weather_info'),
            1 if event_data.get('carpool_enabled') else 0,
            event_data.get('category')
        ))
        await db.commit()
        return cursor.lastrowid

async def get_event(event_id: int) -> Optional[Dict]:
    """Возвращает мероприятие по ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM events WHERE id = ?", (event_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def update_event_message_id(event_id: int, thread_id: int, message_id: int):
    """Сохраняет thread_id и message_id после публикации."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE events SET thread_id = ?, message_id = ? WHERE id = ?",
                         (thread_id, message_id, event_id))
        await db.commit()

async def get_active_events() -> List[Dict]:
    """Возвращает все активные мероприятия (status='active')."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM events WHERE status = 'active'") as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

# ----- Функции для участников -----
async def add_participant(event_id: int, user_id: int, status: str = 'going', car_seats: int = None, passenger_of: int = None):
    """Добавляет участника в событие."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Проверяем, не состоит ли уже
        async with db.execute("SELECT id FROM participants WHERE event_id = ? AND user_id = ?", (event_id, user_id)) as cursor:
            if await cursor.fetchone():
                return False
        await db.execute("""
            INSERT INTO participants (event_id, user_id, status, car_seats, passenger_of)
            VALUES (?, ?, ?, ?, ?)
        """, (event_id, user_id, status, car_seats, passenger_of))
        await db.commit()
        return True

async def remove_participant(event_id: int, user_id: int):
    """Удаляет участника из события."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM participants WHERE event_id = ? AND user_id = ?", (event_id, user_id))
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

async def move_from_waitlist(event_id: int):
    """Перемещает первого из резерва в основной список, если есть место."""
    event = await get_event(event_id)
    if not event or event['status'] != 'active':
        return None
    going = await get_participants(event_id, 'going')
    if len(going) >= event['limit']:
        return None
    # Получаем первого в очереди резерва (по id)
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM participants WHERE event_id = ? AND status = 'waitlist' ORDER BY id ASC LIMIT 1",
                              (event_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                user_id = row[0]
                await db.execute("UPDATE participants SET status = 'going' WHERE event_id = ? AND user_id = ?",
                                 (event_id, user_id))
                await db.commit()
                return user_id
    return None

# ----- Функции для тем форума -----
async def get_forum_topics(bot, chat_id: int):
    """Возвращает список тем форума."""
    topics = await bot.get_forum_topics(chat_id)
    return topics

# ----- Вспомогательные функции -----
async def update_event_status(event_id: int, status: str):
    """Обновляет статус мероприятия (active/completed/cancelled)."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE events SET status = ? WHERE id = ?", (status, event_id))
        await db.commit()