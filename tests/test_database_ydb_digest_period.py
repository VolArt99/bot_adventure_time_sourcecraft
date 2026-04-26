import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch

from bot import database_ydb


class _FakeTx:
    def __init__(self, rows):
        self._rows = rows

    async def execute(self, query, parameters=None, commit_tx=False, settings=None):
        return [SimpleNamespace(rows=self._rows)]


class _FakeSession:
    def __init__(self, rows):
        self._rows = rows

    def transaction(self):
        return _FakeTx(self._rows)


class _FakePool:
    def __init__(self, rows):
        self._rows = rows

    async def retry_operation(self, fn):
        return await fn(_FakeSession(self._rows))


class DigestDatetimeTests(unittest.IsolatedAsyncioTestCase):
    async def test_get_events_for_digest_handles_aware_datetimes(self):
        future_dt = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        fake_rows = [
            SimpleNamespace(
                id=1,
                title="Test",
                status="active",
                date_time=future_dt,
                creator_id=123,
            )
        ]

        with patch("bot.database_ydb.get_pool", return_value=_FakePool(fake_rows)):
            events = await database_ydb.get_events_for_digest(period="all")

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["id"], 1)


if __name__ == "__main__":
    unittest.main()
