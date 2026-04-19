import unittest

from aiogram.fsm.storage.base import StorageKey

from bot.fsm_storage_ydb import YdbStorage


class YdbStorageKeyParamsTests(unittest.TestCase):
    def test_key_parameters_uses_defaults_for_missing_numeric_values(self):
        key = StorageKey(
            bot_id=None,
            chat_id=123,
            user_id=456,
            thread_id=None,
            business_connection_id=None,
            destiny="default",
        )

        params = YdbStorage._key_parameters(key)

        self.assertEqual(params["bot_id"], 0)
        self.assertEqual(params["chat_id"], 123)
        self.assertEqual(params["user_id"], 456)
        self.assertIsNone(params["thread_id"])
        self.assertEqual(params["destiny"], "default")


    def test_key_parameters_fallback_for_mapping_without_bot_id(self):
        params = YdbStorage._key_parameters({
            "chat_id": "321",
            "user_id": "654",
            "destiny": None,
        })

        self.assertEqual(params["bot_id"], 0)
        self.assertEqual(params["chat_id"], 321)
        self.assertEqual(params["user_id"], 654)
        self.assertEqual(params["destiny"], "default")

        
    def test_key_parameters_normalizes_string_ints(self):
        key = StorageKey(
            bot_id="777",
            chat_id="1001",
            user_id="1002",
            thread_id="1003",
            business_connection_id=None,
            destiny="",
        )

        params = YdbStorage._key_parameters(key)

        self.assertEqual(params["bot_id"], 777)
        self.assertEqual(params["chat_id"], 1001)
        self.assertEqual(params["user_id"], 1002)
        self.assertEqual(params["thread_id"], 1003)
        self.assertEqual(params["destiny"], "default")


if __name__ == "__main__":
    unittest.main()