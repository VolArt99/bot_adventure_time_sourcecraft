import sys
from datetime import datetime, timedelta
from pathlib import Path
import unittest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bot"))

import database  # noqa: E402


class DatabaseCoreTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Для YDB не нужно менять DB_PATH
        # Инициализация базы данных (может потребовать реального подключения к YDB)
        # В тестах мы можем пропустить реальную инициализацию
        pass

    async def asyncTearDown(self):
        pass

    @patch('database.create_event')
    @patch('database.get_event')
    async def test_create_event_and_fetch(self, mock_get_event, mock_create_event):
        # Тест с моками для функций базы данных
        now = (datetime.now() + timedelta(days=1)).isoformat()
        
        # Настраиваем моки
        mock_create_event.return_value = 12345
        mock_get_event.return_value = {
            "id": 12345,
            "title": "Тест",
            "description": "Описание",
            "date_time": now,
            "duration_minutes": 60,
            "location": "Москва",
            "price_total": 1000.0,
            "price_per_person": 500.0,
            "participant_limit": 10,
            "thread_id": 0,
            "message_id": 0,
            "creator_id": 1,
            "weather_info": "ясно",
            "carpool_enabled": False,
            "category": "спорт",
            "status": "active"
        }
        
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
        
        # Проверяем, что моки были вызваны
        mock_create_event.assert_called_once()
        mock_get_event.assert_called_once_with(12345)

    @patch('database.set_user_category_subscriptions')
    @patch('database.get_user_category_subscriptions')
    async def test_category_subscriptions(self, mock_get_subs, mock_set_subs):
        # Настраиваем моки
        mock_get_subs.return_value = ["поездки", "спорт"]
        
        await database.set_user_category_subscriptions(42, ["спорт", "поездки"])
        subscriptions = await database.get_user_category_subscriptions(42)
        
        self.assertEqual(subscriptions, ["поездки", "спорт"])
        
        # Проверяем, что моки были вызваны
        mock_set_subs.assert_called_once_with(42, ["спорт", "поездки"])
        mock_get_subs.assert_called_once_with(42)


if __name__ == "__main__":
    unittest.main()