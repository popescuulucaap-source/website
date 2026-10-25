import unittest
from unittest.mock import patch

import psycopg
import app as website


class DatabaseDegradationTests(unittest.TestCase):
    def test_homepage_uses_cached_content_when_database_is_unavailable(self):
        with (
            patch.object(website, "DATABASE_URL", "postgresql://unavailable"),
            patch.object(website, "db_connect", side_effect=psycopg.OperationalError("quota exceeded")),
            patch.object(website, "bot_guild_snapshot", return_value=[]),
        ):
            response = website.app.test_client().get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Guard with Gargand", response.data)

    def test_public_catalogs_fall_back_to_memory(self):
        with (
            patch.object(website, "DATABASE_URL", "postgresql://unavailable"),
            patch.object(website, "db_connect", side_effect=psycopg.OperationalError("quota exceeded")),
        ):
            self.assertEqual(website.load_developers(), website.present_developers(website.MEMORY_DEVELOPERS))
            self.assertEqual(website.load_announcements(), [])
            self.assertEqual(website.load_custom_commands(), [])

    def test_health_reports_database_degradation_without_failing_process_health(self):
        with (
            patch.object(website, "DATABASE_URL", "postgresql://unavailable"),
            patch.object(website, "db_connect", side_effect=psycopg.OperationalError("quota exceeded")),
        ):
            response = website.app.test_client().get("/health")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["ok"])
        self.assertTrue(payload["degraded"])
        self.assertFalse(payload["database"]["reachable"])


if __name__ == "__main__":
    unittest.main()
