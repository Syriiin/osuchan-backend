from unittest.mock import Mock, patch

import pytest
from django.http import HttpRequest
from django.test import RequestFactory

from middleware.logging import DiscordErrorLoggingMiddleware


class TestDiscordErrorLoggingMiddleware:
    @pytest.fixture
    def middleware(self):
        def get_response(request: HttpRequest):
            return f"testresponse for {request.path}"

        return DiscordErrorLoggingMiddleware(get_response)

    def test_call(self, rf: RequestFactory, middleware: DiscordErrorLoggingMiddleware):
        response = middleware(rf.get("/testpath"))
        assert response == "testresponse for /testpath"

    @patch("middleware.logging.ErrorReporter.report_error")
    def test_process_exception(
        self,
        report_error_mock: Mock,
        rf: RequestFactory,
        middleware: DiscordErrorLoggingMiddleware,
    ):
        test_exception = Exception("testexception")
        middleware.process_exception(
            rf.post("/testpath", data={"testkey": "testvalue"}), test_exception
        )
        report_error_mock.assert_called_once()
        assert report_error_mock.call_args.args[0] == test_exception
        assert (
            report_error_mock.call_args.kwargs["title"]
            == f"Exception occured in request `POST /testpath`"
        )
        assert "testkey" in report_error_mock.call_args.kwargs["extra_details"]
        assert "testvalue" in report_error_mock.call_args.kwargs["extra_details"]
