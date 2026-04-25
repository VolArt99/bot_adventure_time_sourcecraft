import unittest

from bot import database_ydb


class YdbQueryPatchTests(unittest.TestCase):
    def test_normalize_parameters_adds_prefix_and_types(self):
        params, types = database_ydb._normalize_parameters({"user_id": 123, "name": "alice"})

        self.assertEqual(params["$user_id"], 123)
        self.assertEqual(params["$name"], "alice")
        self.assertEqual(types["$user_id"], database_ydb.ydb.PrimitiveType.Int64)
        self.assertEqual(types["$name"], database_ydb.ydb.PrimitiveType.Utf8)

    def test_normalize_parameters_uses_uint64_for_limit(self):
        _, types = database_ydb._normalize_parameters({"limit": 10})

        self.assertEqual(types["$limit"], database_ydb.ydb.PrimitiveType.Uint64)
        
    def test_build_query_with_declares_when_missing(self):
        query = "SELECT * FROM users WHERE id = $user_id;"
        rendered = database_ydb._build_query_with_declares(
            query,
            {"$user_id": database_ydb.ydb.PrimitiveType.Int64},
        )

        self.assertIn("DECLARE $user_id AS Int64;", rendered)
        self.assertTrue(rendered.strip().endswith(query))

    def test_build_query_with_declares_keeps_existing_declare(self):
        query = "DECLARE $user_id AS Int64;\nSELECT * FROM users WHERE id = $user_id;"
        rendered = database_ydb._build_query_with_declares(
            query,
            {"$user_id": database_ydb.ydb.PrimitiveType.Int64},
        )

        self.assertEqual(rendered, query)


if __name__ == "__main__":
    unittest.main()
