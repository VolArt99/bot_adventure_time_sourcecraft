import sys
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bot"))

import database  # noqa: E402


class DatabaseCoreTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.old_db_path = database.DB_PATH
        database.DB_PATH = str(Path(self.tmp_dir.name) / "events_test.db")
        await database.init_db()

    async def asyncTearDown(self):
        database.DB_PATH = self.old_db_path
        self.tmp_dir.cleanup()

    async def test_create_event_and_fetch(self):
        now = (datetime.now() + timedelta(days=1)).isoformat()
        event_id = await database.create_event(
            {
                "title": "Тест",
                "description": "Описание",
                "date_time": now,
                "duration_minutes": 60,
                "location": "Москва",
                "price_total": 1000,
                "price_per_person": 500,
                "participant_limit": 10,
                "thread_id": None,
                "message_id": None,
                "creator_id": 1,
                "weather_info": "ясно",
                "carpool_enabled": False,
                "category": "спорт",
            }
        )
        event = await database.get_event(event_id)
        self.assertEqual(event["title"], "Тест")

    async def test_category_subscriptions(self):
        await database.set_user_category_subscriptions(42, ["спорт", "поездки"])
        subscriptions = await database.get_user_category_subscriptions(42)
        self.assertEqual(subscriptions, ["поездки", "спорт"])


if __name__ == "__main__":
    unittest.main()
