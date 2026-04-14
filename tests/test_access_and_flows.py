import os
import importlib
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

os.environ.setdefault("BOT_TOKEN", "test-token")
os.environ.setdefault("OWNER_ID", "12345")
from bot.middleware.command_access import CommandAccessMiddleware  # noqa: E402

common = importlib.import_module("bot.handlers.common")
participation = importlib.import_module("bot.handlers.participation")

class _FakeMessage:
    def __init__(self, user_id: int, text: str, chat_type: str = "private"):
        self.text = text
        self.chat = SimpleNamespace(type=chat_type)
        self.from_user = SimpleNamespace(id=user_id)
        self.answer = AsyncMock()


class _FakeCallback:
    def __init__(self, user_id: int, data: str):
        self.from_user = SimpleNamespace(id=user_id, username="u", first_name="A", last_name="B")
        self.data = data
        self.answer = AsyncMock()
        self.message = SimpleNamespace(edit_text=AsyncMock(), answer=AsyncMock())
        self.bot = SimpleNamespace(
            create_chat_invite_link=AsyncMock(return_value=SimpleNamespace(invite_link="https://t.me/+invite")),
            send_message=AsyncMock(),
        )


class CommandAccessTests(unittest.IsolatedAsyncioTestCase):
    async def test_outsider_help_command_is_allowed(self):
        m = CommandAccessMiddleware()
        event = _FakeMessage(user_id=777, text="/help")
        handler = AsyncMock()

        with (
            patch("bot.middleware.command_access.Message", _FakeMessage),
            patch("bot.middleware.command_access.is_member_approved", new=AsyncMock(return_value=False)),
        ):
            await m(handler, event, {})

        handler.assert_awaited()
        event.answer.assert_not_awaited()


class OnboardingOwnerChecksTests(unittest.IsolatedAsyncioTestCase):
    async def test_approve_requires_owner_id(self):
        callback = _FakeCallback(user_id=999999, data="approve_user_42")

        await common.owner_approve_user(callback)

        callback.answer.assert_awaited()
        callback.bot.create_chat_invite_link.assert_not_awaited()

    async def test_reject_flow_for_owner(self):
        owner_callback = _FakeCallback(user_id=common.OWNER_ID, data="reject_user_42")

        with patch("bot.handlers.common.delete_pending_user", new=AsyncMock()) as delete_pending_user:
            await common.owner_reject_user(owner_callback)

        delete_pending_user.assert_awaited_once_with(42)
        owner_callback.bot.send_message.assert_awaited()
        owner_callback.message.edit_text.assert_awaited()


class ParticipationTransitionsTests(unittest.IsolatedAsyncioTestCase):
    async def test_waitlist_denied_if_already_in_main_list(self):
        callback = _FakeCallback(user_id=11, data="waitlist_100")

        with (
            patch("bot.handlers.participation.get_event", new=AsyncMock(return_value={"id": 100, "status": "active"})),
            patch("bot.handlers.participation.get_main_participants", new=AsyncMock(return_value=[11])),
        ):
            await participation.waitlist_event(callback)

        callback.answer.assert_awaited()


if __name__ == "__main__":
    unittest.main()
