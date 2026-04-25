import os
import unittest

os.environ.setdefault("BOT_TOKEN", "test-token")
os.environ.setdefault("OWNER_ID", "12345")

from bot.handlers.common_feature.views import build_help_text


class HelpTextHtmlTests(unittest.TestCase):
    def test_help_text_does_not_contain_unescaped_placeholders(self):
        text = build_help_text(is_admin_or_owner=True)

        self.assertNotIn("<текст>", text)
        self.assertNotIn("<id>", text)
        self.assertIn("&lt;текст&gt;", text)
        self.assertIn("&lt;id&gt;", text)


if __name__ == "__main__":
    unittest.main()
