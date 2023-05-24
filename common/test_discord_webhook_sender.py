from unittest import TestCase
from unittest.mock import Mock, patch

from common.discord_webhook_sender import (
    InvalidWebhookUrlError,
    LiveDiscordWebhookSender,
)


class LiveDiscordWebhookSenderTestCase(TestCase):
    def setUp(self) -> None:
        self.webhook_sender = LiveDiscordWebhookSender()

    @patch("common.discord_webhook_sender.httpx.post")
    def test_send(self, post_mock: Mock):
        test_webhook_url = "https://discord.com/api/webhooks/fakewebhook"
        test_data = {"testkey": "testvalue"}
        self.webhook_sender.send(test_webhook_url, test_data)

        post_mock.assert_called_once()
        self.assertEqual(test_webhook_url, post_mock.call_args.args[0])
        self.assertEqual(test_data, post_mock.call_args.kwargs["json"])

    @patch("common.discord_webhook_sender.httpx.post")
    def test_send_raises_exception_for_invalid_url(self, post_mock: Mock):
        test_data = {"testkey": "testvalue"}
        self.assertRaises(
            InvalidWebhookUrlError,
            self.webhook_sender.send,
            "notadiscordwebhook",
            test_data,
        )
        post_mock.assert_not_called()
