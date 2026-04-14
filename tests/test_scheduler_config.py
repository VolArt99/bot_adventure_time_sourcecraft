import os
import sys
from pathlib import Path
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
import types

os.environ.setdefault("BOT_TOKEN", "test-token")
os.environ.setdefault("DIGEST_DAY_OF_WEEK", "3")
os.environ.setdefault("DIGEST_HOUR", "14")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bot"))

from utils import scheduler  # noqa: E402


class SchedulerConfigTests(unittest.IsolatedAsyncioTestCase):
    async def test_schedule_digest_uses_config_values(self):
        fake_bot = object()
        fake_digest_module = types.SimpleNamespace(send_digest=AsyncMock())
        with (
            patch.dict(sys.modules, {"handlers.digest": fake_digest_module}),
            patch("utils.scheduler.DIGEST_DAY_OF_WEEK", 3),
            patch("utils.scheduler.DIGEST_HOUR", 14),
            patch.object(scheduler.scheduler, "add_job") as add_job,
        ):
            await scheduler.schedule_digest(fake_bot, chat_id=1, thread_id=2)

        _, kwargs = add_job.call_args
        self.assertEqual(kwargs["day_of_week"], 2)
        self.assertEqual(kwargs["hour"], 14)

    async def test_reminder_is_sent_in_html(self):
        bot = SimpleNamespace(send_message=AsyncMock())

        with (
            patch("utils.scheduler.get_event", new=AsyncMock(return_value={
                "id": 100,
                "status": "active",
                "title": "Событие",
                "date_time": "2026-06-01T10:00:00+00:00",
                "thread_id": 10,
            })),
            patch("utils.scheduler.get_participants", new=AsyncMock(return_value=[123])),
        ):
            await scheduler.send_reminder(100, 3600, bot)

        parse_modes = [c.kwargs.get("parse_mode") for c in bot.send_message.await_args_list]
        self.assertTrue(parse_modes)
        self.assertTrue(all(mode == "HTML" for mode in parse_modes))


if __name__ == "__main__":
    unittest.main()
