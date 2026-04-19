"""FSM storage for aiogram backed by YDB."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from aiogram.fsm.state import State
from aiogram.fsm.storage.base import BaseStorage, StorageKey

from bot.database import get_pool


class YdbStorage(BaseStorage):
    """Persist FSM state/data in YDB table `fsm_states`."""

    @staticmethod
    def _key_parameters(key: StorageKey) -> dict[str, Any]:
        """Build stable YDB parameters for FSM key.

        В aiogram `bot_id` может быть `None` (зависит от key builder/стратегии),
        но в нашей таблице `fsm_states.bot_id` объявлен как `NOT NULL`.
        Для такого случая используем стабильный fallback `0`, чтобы параметр
        всегда передавался в запрос и не приводил к `Missing value for parameter`.
        """
        return {
            "bot_id": key.bot_id if key.bot_id is not None else 0,
            "chat_id": key.chat_id,
            "user_id": key.user_id,
            "thread_id": key.thread_id,
            "business_connection_id": key.business_connection_id,
            "destiny": key.destiny,
        }

    async def set_state(self, key: StorageKey, state: str | State | None = None) -> None:
        state_value = state.state if isinstance(state, State) else state
        pool = await get_pool()
        await pool.retry_operation(
            lambda session: session.transaction().execute(
                """
                DECLARE $bot_id AS Int64;
                DECLARE $chat_id AS Int64;
                DECLARE $user_id AS Int64;
                DECLARE $thread_id AS Int64?;
                DECLARE $business_connection_id AS Utf8?;
                DECLARE $destiny AS Utf8;
                DECLARE $state AS Utf8?;

                UPSERT INTO fsm_states (
                    bot_id, chat_id, user_id, thread_id, business_connection_id, destiny, state
                ) VALUES (
                    $bot_id, $chat_id, $user_id, $thread_id, $business_connection_id, $destiny, $state
                );
                """,
                parameters={
                    **self._key_parameters(key),
                    "state": state_value,
                },
                commit_tx=True,
            )
        )

    async def get_state(self, key: StorageKey) -> str | None:
        pool = await get_pool()
        result = await pool.retry_operation(
            lambda session: session.transaction().execute(
                """
                DECLARE $bot_id AS Int64;
                DECLARE $chat_id AS Int64;
                DECLARE $user_id AS Int64;
                DECLARE $thread_id AS Int64?;
                DECLARE $business_connection_id AS Utf8?;
                DECLARE $destiny AS Utf8;

                SELECT state FROM fsm_states
                WHERE bot_id = $bot_id
                  AND chat_id = $chat_id
                  AND user_id = $user_id
                  AND thread_id IS NOT DISTINCT FROM $thread_id
                  AND business_connection_id IS NOT DISTINCT FROM $business_connection_id
                  AND destiny = $destiny;
                """,
                parameters=self._key_parameters(key),
                commit_tx=True,
            )
        )
        rows = result[0].rows
        if not rows:
            return None
        return rows[0].state

    async def set_data(self, key: StorageKey, data: Mapping[str, Any]) -> None:
        serialized = json.dumps(dict(data), ensure_ascii=False)
        pool = await get_pool()
        await pool.retry_operation(
            lambda session: session.transaction().execute(
                """
                DECLARE $bot_id AS Int64;
                DECLARE $chat_id AS Int64;
                DECLARE $user_id AS Int64;
                DECLARE $thread_id AS Int64?;
                DECLARE $business_connection_id AS Utf8?;
                DECLARE $destiny AS Utf8;
                DECLARE $data_json AS Utf8?;

                UPSERT INTO fsm_states (
                    bot_id, chat_id, user_id, thread_id, business_connection_id, destiny, data_json
                ) VALUES (
                    $bot_id, $chat_id, $user_id, $thread_id, $business_connection_id, $destiny, $data_json
                );
                """,
                parameters={
                    **self._key_parameters(key),
                    "data_json": serialized,
                },
                commit_tx=True,
            )
        )

    async def get_data(self, key: StorageKey) -> dict[str, Any]:
        pool = await get_pool()
        result = await pool.retry_operation(
            lambda session: session.transaction().execute(
                """
                DECLARE $bot_id AS Int64;
                DECLARE $chat_id AS Int64;
                DECLARE $user_id AS Int64;
                DECLARE $thread_id AS Int64?;
                DECLARE $business_connection_id AS Utf8?;
                DECLARE $destiny AS Utf8;

                SELECT data_json FROM fsm_states
                WHERE bot_id = $bot_id
                  AND chat_id = $chat_id
                  AND user_id = $user_id
                  AND thread_id IS NOT DISTINCT FROM $thread_id
                  AND business_connection_id IS NOT DISTINCT FROM $business_connection_id
                  AND destiny = $destiny;
                """,
                parameters=self._key_parameters(key),
                commit_tx=True,
            )
        )
        rows = result[0].rows
        if not rows:
            return {}

        data_json = rows[0].data_json
        if not data_json:
            return {}

        try:
            data = json.loads(data_json)
        except json.JSONDecodeError:
            return {}

        return data if isinstance(data, dict) else {}

    async def close(self) -> None:
        """No-op: YDB pool lifecycle is controlled by database module."""
        return None
