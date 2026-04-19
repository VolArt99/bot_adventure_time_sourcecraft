import unittest

from bot.database_ydb import _is_schema_limit_error


class DatabaseYdbSchemaLimitsTests(unittest.TestCase):
    def test_detects_schema_limit_phrase(self):
        exc = RuntimeError("Request exceeded a limit on the number of schema operations, try again later.")
        self.assertTrue(_is_schema_limit_error(exc))

    def test_detects_server_code(self):
        exc = RuntimeError("GenericError (server_code: 400080)")
        self.assertTrue(_is_schema_limit_error(exc))

    def test_ignores_unrelated_error(self):
        exc = RuntimeError("Permission denied")
        self.assertFalse(_is_schema_limit_error(exc))


if __name__ == "__main__":
    unittest.main()
