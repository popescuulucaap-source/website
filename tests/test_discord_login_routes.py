import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import app as website


class DiscordLoginRouteTests(unittest.TestCase):
    def test_login_uses_the_registered_oauth_callback(self):
        with (
            patch.object(website, "DISCORD_CLIENT_ID", "test-client-id"),
            patch.object(website, "DISCORD_CLIENT_SECRET", "test-client-secret"),
            patch.object(website, "DISCORD_REDIRECT_URI", "https://gargand-bot.onrender.com/oauth/callback"),
        ):
            response = website.app.test_client().get("/login")

        self.assertEqual(response.status_code, 302)
        location = urlparse(response.headers["Location"])
        self.assertEqual(location.netloc, "discord.com")
        self.assertEqual(location.path, "/oauth2/authorize")
        query = parse_qs(location.query)
        self.assertEqual(query["redirect_uri"], ["https://gargand-bot.onrender.com/oauth/callback"])

    def test_oauth_callback_accepts_trailing_slash_and_disables_caching(self):
        response = website.app.test_client().get("/oauth/callback/")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.headers["Cache-Control"], "no-store, max-age=0")
        self.assertIn(b"could not be verified", response.data)


if __name__ == "__main__":
    unittest.main()
