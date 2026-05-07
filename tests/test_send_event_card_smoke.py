import importlib
import os
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

os.environ.setdefault("BOT_TOKEN", "test-token")
os.environ.setdefault("OWNER_ID", "12345")

my_events = importlib.import_module("bot.handlers.my_events")


class SendEventCardSmokeTests(unittest.IsolatedAsyncioTestCase):
    async def test_send_event_card_imports_keyboard_and_sends_card(self):
        message = SimpleNamespace(
            text="/send_event_card 100",
            from_user=SimpleNamespace(id=777),
            answer=AsyncMock(),
            bot=SimpleNamespace(
                send_message=AsyncMock(return_value=SimpleNamespace(message_id=555)),
            ),
        )
        event = {
            "id": 100,
            "chat_id": -100123,
            "thread_id": 42,
            "creator_id": 777,
            "responsible_id": None,
            "carpool_enabled": True,
            "date_time": "2026-06-01T12:00:00+00:00",
            "title": "Board games",
            "location": "Cafe",
            "message_id": 321,
        }

        with (
            patch("bot.handlers.my_events.get_event", new=AsyncMock(return_value=event)),
            patch("bot.handlers.participation.build_event_text", new=AsyncMock(return_value="<b>card</b>")),
            patch("bot.handlers.my_events.get_topic_name_by_thread_id", new=AsyncMock(return_value="Игры")),
        ):
            await my_events.cmd_send_event_card(message)

        message.bot.send_message.assert_awaited_once()
        _, kwargs = message.bot.send_message.await_args
        self.assertEqual(kwargs["chat_id"], -100123)
        self.assertEqual(kwargs["message_thread_id"], 42)
        self.assertIn("Board games", kwargs["text"])
        self.assertIn("открыть основную карточку", kwargs["text"])
        self.assertNotIn("reply_markup", kwargs)
        message.answer.assert_awaited_once_with("✅ Короткое сообщение со ссылкой отправлено (message_id: 555).")


if __name__ == "__main__":
    unittest.main()
