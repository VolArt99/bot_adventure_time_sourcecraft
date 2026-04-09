import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bot"))

from texts import format_duration, category_to_hashtags  # noqa: E402


class TextFormattersTest(unittest.TestCase):
    def test_format_duration_hours_and_minutes(self):
        self.assertEqual(format_duration(90), "1 ч 30 мин")

    def test_format_duration_empty(self):
        self.assertEqual(format_duration(None), "не указана")

    def test_category_to_hashtags(self):
        self.assertEqual(
            category_to_hashtags("спорт, поездки"),
            "#спорт #поездки",
        )


if __name__ == "__main__":
    unittest.main()
