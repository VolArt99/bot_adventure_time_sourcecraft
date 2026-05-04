from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock

from bot.utils.ui import (
    PRIVATE_INTERMEDIATE_MESSAGE_IDS_KEY,
    answer_private_final,
    answer_private_intermediate,
)


class FakeState:
    def __init__(self):
        self.data = {}

    async def get_data(self):
        return dict(self.data)

    async def update_data(self, **kwargs):
        self.data.update(kwargs)


class FakeMessage:
    def __init__(self):
        self.chat = SimpleNamespace(id=42, type="private")
        self.bot = SimpleNamespace(delete_message=AsyncMock())
        self.answer = AsyncMock()


def _sent_message(message_id: int):
    return SimpleNamespace(message_id=message_id)


class PrivateIntermediateMessagesTests(IsolatedAsyncioTestCase):
    async def test_next_private_intermediate_deletes_previous_bot_prompt(self):
        state = FakeState()
        message = FakeMessage()
        message.answer.side_effect = [_sent_message(101), _sent_message(102)]

        await answer_private_intermediate(message, state, "step 1")
        await answer_private_intermediate(message, state, "step 2")

        message.bot.delete_message.assert_awaited_once_with(chat_id=42, message_id=101)
        self.assertEqual(state.data[PRIVATE_INTERMEDIATE_MESSAGE_IDS_KEY], [102])

    async def test_private_final_deletes_pending_prompt_but_is_not_marked_for_deletion(self):
        state = FakeState()
        state.data[PRIVATE_INTERMEDIATE_MESSAGE_IDS_KEY] = [201]
        message = FakeMessage()
        message.answer.return_value = _sent_message(202)

        await answer_private_final(message, state, "done")

        message.bot.delete_message.assert_awaited_once_with(chat_id=42, message_id=201)
        message.answer.assert_awaited_once_with("done")
        self.assertEqual(state.data[PRIVATE_INTERMEDIATE_MESSAGE_IDS_KEY], [])

    async def test_group_intermediate_is_not_tracked_or_deleted(self):
        state = FakeState()
        message = FakeMessage()
        message.chat.type = "group"
        message.answer.return_value = _sent_message(301)

        await answer_private_intermediate(message, state, "group reply")

        message.bot.delete_message.assert_not_awaited()
        self.assertNotIn(PRIVATE_INTERMEDIATE_MESSAGE_IDS_KEY, state.data)
