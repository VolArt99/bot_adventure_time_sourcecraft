import unittest
from types import SimpleNamespace
from unittest.mock import patch

from bot import database_ydb


class _FakeTx:
    def __init__(self, collector):
        self._collector = collector

    async def execute(self, query, parameters=None, commit_tx=False, settings=None):
        self._collector.append(
            {
                "query": query,
                "parameters": parameters,
                "commit_tx": commit_tx,
            }
        )
        return [SimpleNamespace(rows=[])]


class _FakeSession:
    def __init__(self, collector):
        self._collector = collector

    def transaction(self):
        return _FakeTx(self._collector)


class _FakePool:
    def __init__(self):
        self.calls = []

    async def retry_operation(self, fn):
        return await fn(_FakeSession(self.calls))


class UserEventsQueryTests(unittest.IsolatedAsyncioTestCase):
    async def test_all_user_events_query_uses_exists_instead_of_left_join_predicate(self):
        fake_pool = _FakePool()

        with patch("bot.database_ydb.get_pool", return_value=fake_pool):
            await database_ydb.get_user_events(user_id=42, status="active")

        self.assertEqual(len(fake_pool.calls), 1)
        query = fake_pool.calls[0]["query"]
        self.assertIn("EXISTS (", query)
        self.assertNotIn("LEFT JOIN participants", query)
        self.assertEqual(fake_pool.calls[0]["parameters"], {"user_id": 42})


if __name__ == "__main__":
    unittest.main()
