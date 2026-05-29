import os
import unittest
from datetime import datetime

os.environ.setdefault("BOT_TOKEN", "test-token")

from bot.texts import format_duration, format_event_period, category_to_hashtags, category_to_branded_hashtags  # noqa: E402
from bot.utils.event_links import build_google_calendar_link, build_maps_link  # noqa: E402
from bot.utils.pairing import build_random_pairs  # noqa: E402

class TextFormattersTest(unittest.TestCase):
    def test_format_duration_hours_and_minutes(self):
        self.assertEqual(format_duration(90), "1 ч 30 мин")

    def test_format_duration_empty(self):
        self.assertEqual(format_duration(None), "не указана")

    def test_category_to_hashtags(self):
        self.assertEqual(category_to_hashtags("спорт, поездки"), "#спорт #поездки")

    def test_category_to_branded_hashtags(self):
        self.assertEqual(category_to_branded_hashtags("настолки, книжный клуб"), "🎲 #настолки 📚 #книжный_клуб")

    def test_format_event_period(self):
        start_dt = datetime.fromisoformat("2026-06-01T10:00:00+03:00")
        text = format_event_period(start_dt, "2026-06-30T23:59:00+03:00")
        self.assertEqual(text, "📆 Период: 01.06.2026 10:00 — 30.06.2026 23:59")

    def test_format_event_period_empty_for_regular_event(self):
        start_dt = datetime.fromisoformat("2026-06-01T10:00:00+03:00")
        self.assertIsNone(format_event_period(start_dt, None))
        self.assertIsNone(format_event_period(start_dt, ""))

class FeatureHelpersTest(unittest.TestCase):
    def test_maps_and_calendar_links(self):
        event = {
            "id": 1,
            "title": "Вело",
            "description": "Тренировка",
            "location": "Санкт-Петербург, Невский 1",
            "date_time": "2026-06-01T10:00:00",
            "duration_minutes": 90,
            "period_end": "2026-06-05T10:00:00",
        }

        calendar_link = build_google_calendar_link(event)
        
        self.assertIn("google.com/maps", build_maps_link(event["location"]))
        self.assertIn("calendar.google.com", calendar_link)
        self.assertIn("dates=20260601T100000%2F20260605T100000", calendar_link)

    def test_regular_event_calendar_link_uses_duration_without_period(self):
        event = {
            "title": "Вело",
            "date_time": "2026-06-01T10:00:00",
            "duration_minutes": 90,
            "period_end": "",
        }

        calendar_link = build_google_calendar_link(event)

        self.assertIn("dates=20260601T100000%2F20260601T113000", calendar_link)

    def test_build_random_pairs(self):
        pairs, leftovers = build_random_pairs([1, 2, 3])
        self.assertEqual(len(pairs), 1)
        self.assertEqual(len(leftovers), 1)
        

if __name__ == "__main__":
    unittest.main()
