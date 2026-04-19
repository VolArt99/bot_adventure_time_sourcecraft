import os
import unittest
from unittest.mock import patch


from bot.init_flags import should_run_schema_init


class MainInitFlagsTests(unittest.TestCase):
    def test_auto_init_db_override_true(self):
        with patch.dict(os.environ, {"AUTO_INIT_DB": "true"}, clear=False):
            self.assertTrue(should_run_schema_init())

    def test_auto_init_db_override_false(self):
        with patch.dict(os.environ, {"AUTO_INIT_DB": "0"}, clear=False):
            self.assertFalse(should_run_schema_init())

    def test_default_disabled_in_cloud_function(self):
        with patch.dict(os.environ, {"FUNCTION_ID": "fn-id"}, clear=False):
            os.environ.pop("AUTO_INIT_DB", None)
            self.assertFalse(should_run_schema_init())


if __name__ == "__main__":
    unittest.main()
