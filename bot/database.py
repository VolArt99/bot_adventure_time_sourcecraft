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