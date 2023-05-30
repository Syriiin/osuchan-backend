from datetime import datetime, timezone
from unittest.mock import create_autospec

import pytest
from django.http import HttpRequest
from django.test import RequestFactory
from freezegun import freeze_time

from osuauth.middleware import LastActiveMiddleware
from osuauth.models import User


class TestLastActiveMiddleware:
    @pytest.fixture
    def middleware(self):
        def get_response(request: HttpRequest):
            return f"testresponse for {request.path}"

        return LastActiveMiddleware(get_response)

    @freeze_time("2023-01-01")
    def test_call(self, rf: RequestFactory, middleware: LastActiveMiddleware):
        request = rf.get("/testpath")
        request.user = create_autospec(spec=User)

        response = middleware(request)

        assert response == "testresponse for /testpath"
        assert request.user.last_active == datetime(2023, 1, 1, tzinfo=timezone.utc)
        request.user.save.assert_called_once()
