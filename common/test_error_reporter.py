from unittest.mock import Mock, patch

import pytest

from common.error_reporter import DiscordErrorReporter


class TestDiscordErrorReporter:
    @pytest.fixture
    def error_reporter(self):
        return DiscordErrorReporter()

    @patch(
        "common.error_reporter.settings.DISCORD_WEBHOOK_URL_ERROR_LOG",
        "testwebhookurl",
    )
    @patch("common.error_reporter.httpx.post", return_value=None)
    def test_report_error(self, post_mock: Mock, error_reporter: DiscordErrorReporter):
        error_reporter.report_error(
            Exception("testexception"), "testtitle", "testextra"
        )

        post_mock.assert_called_once()
        assert "testwebhookurl" in post_mock.call_args.args[0]
        assert "testexception" in post_mock.call_args.kwargs["data"]["content"]
        assert b"testtitle" in post_mock.call_args.kwargs["files"]["upload-file"][1]
        assert b"testextra" in post_mock.call_args.kwargs["files"]["upload-file"][1]

    @patch(
        "common.error_reporter.settings.DISCORD_WEBHOOK_URL_ERROR_LOG",
        "",
    )
    @patch("common.error_reporter.httpx.post", return_value=None)
    def test_report_error_fails_if_no_url(
        self, post_mock: Mock, error_reporter: DiscordErrorReporter
    ):
        error_reporter.report_error(
            Exception("testexception"), "testtitle", "testextra"
        )

        post_mock.assert_not_called()
