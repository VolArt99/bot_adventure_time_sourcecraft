import os
import unittest

os.environ.setdefault("BOT_TOKEN", "test-token")
os.environ.setdefault("OWNER_ID", "12345")

from bot.handlers.common_feature.views import build_help_text, build_main_menu_text, build_menu_section_text
from bot.utils.design import CARD_DIVIDER


class HelpTextHtmlTests(unittest.TestCase):
    def test_help_text_does_not_contain_unescaped_placeholders(self):
        text = build_help_text(is_admin_or_owner=True)

        self.assertNotIn("<текст>", text)
        self.assertNotIn("<id>", text)
        self.assertIn("&lt;текст&gt;", text)
        self.assertIn("&lt;id&gt;", text)

    def test_help_text_mentions_visual_menu(self):
        text = build_help_text(is_admin_or_owner=False)

        self.assertIn("/menu", text)

    def test_main_menu_text_and_sections_are_styled(self):
        menu_text = build_main_menu_text(is_admin_or_owner=True)
        section_text = build_menu_section_text("create_event", is_admin_or_owner=False)

        self.assertIn("Adventure Time Control Center", menu_text)
        self.assertIn(CARD_DIVIDER, menu_text)
        self.assertIn("🎉 <b>Создание мероприятия</b>", section_text)
        self.assertIn("👉 <i>", section_text)
        

if __name__ == "__main__":
    unittest.main()
