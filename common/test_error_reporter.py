from unittest import TestCase
from unittest.mock import Mock, patch

from common.error_reporter import DiscordErrorReporter


class DiscordErrorReporterTestCase(TestCase):
    def setUp(self) -> None:
        self.error_reporter = DiscordErrorReporter()

    @patch(
        "common.error_reporter.settings.DISCORD_WEBHOOK_URL_ERROR_LOG",
        "testwebhookurl",
    )
    @patch("common.error_reporter.httpx.post", return_value=None)
    def test_report_error(self, post_mock: Mock):
        self.error_reporter.report_error(
            Exception("testexception"), "testtitle", "testextra"
        )

        post_mock.assert_called_once()
        self.assertIn("testwebhookurl", post_mock.call_args.args[0])
        self.assertIn("testexception", post_mock.call_args.kwargs["data"]["content"])
        self.assertIn(
            b"testtitle", post_mock.call_args.kwargs["files"]["upload-file"][1]
        )
        self.assertIn(
            b"testextra", post_mock.call_args.kwargs["files"]["upload-file"][1]
        )

    @patch(
        "common.error_reporter.settings.DISCORD_WEBHOOK_URL_ERROR_LOG",
        "",
    )
    @patch("common.error_reporter.httpx.post", return_value=None)
    def test_report_error_fails_if_no_url(self, post_mock: Mock):
        self.error_reporter.report_error(
            Exception("testexception"), "testtitle", "testextra"
        )

        post_mock.assert_not_called()
