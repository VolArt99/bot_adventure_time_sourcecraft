import os
import sys
from pathlib import Path
import unittest

os.environ.setdefault("BOT_TOKEN", "test-token")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bot"))

from texts import format_duration, category_to_hashtags  # noqa: E402
from utils.event_links import build_google_calendar_link, build_maps_link  # noqa: E402
from utils.pairing import build_random_pairs  # noqa: E402


class TextFormattersTest(unittest.TestCase):
    def test_format_duration_hours_and_minutes(self):
        self.assertEqual(format_duration(90), "1 ч 30 мин")

    def test_format_duration_empty(self):
        self.assertEqual(format_duration(None), "не указана")

    def test_category_to_hashtags(self):
        self.assertEqual(category_to_hashtags("спорт, поездки"), "#спорт #поездки")


class FeatureHelpersTest(unittest.TestCase):
    def test_maps_and_calendar_links(self):
        event = {
            "id": 1,
            "title": "Вело",
            "description": "Тренировка",
            "location": "Санкт-Петербург, Невский 1",
            "date_time": "2026-06-01T10:00:00",
            "duration_minutes": 90,
        }

        self.assertIn("google.com/maps", build_maps_link(event["location"]))
        self.assertIn("calendar.google.com", build_google_calendar_link(event))

    def test_build_random_pairs(self):
        pairs, leftovers = build_random_pairs([1, 2, 3])
        self.assertEqual(len(pairs), 1)
        self.assertEqual(len(leftovers), 1)
        

if __name__ == "__main__":
    unittest.main()
