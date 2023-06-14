from unittest.mock import Mock, patch

import pytest

from common.discord_webhook_sender import (
    InvalidWebhookUrlError,
    LiveDiscordWebhookSender,
)


class TestLiveDiscordWebhookSender:
    @pytest.fixture
    def webhook_sender(self):
        return LiveDiscordWebhookSender()

    @patch("common.discord_webhook_sender.httpx.post")
    def test_send(self, post_mock: Mock, webhook_sender: LiveDiscordWebhookSender):
        test_webhook_url = "https://discord.com/api/webhooks/fakewebhook"
        test_data = {"testkey": "testvalue"}
        webhook_sender.send(test_webhook_url, test_data)

        post_mock.assert_called_once()
        assert test_webhook_url == post_mock.call_args.args[0]
        assert test_data == post_mock.call_args.kwargs["json"]

    @patch("common.discord_webhook_sender.httpx.post")
    def test_send_raises_exception_for_invalid_url(
        self, post_mock: Mock, webhook_sender: LiveDiscordWebhookSender
    ):
        test_data = {"testkey": "testvalue"}
        with pytest.raises(InvalidWebhookUrlError):
            webhook_sender.send("notadiscordwebhook", test_data)
        post_mock.assert_not_called()
