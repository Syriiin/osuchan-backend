from http import HTTPStatus

import pytest
from django.urls import reverse
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory

from common.osu.enums import Gamemode
from profiles.views import GetUserStats


@pytest.mark.django_db
class TestGetUserStats:
    @pytest.fixture
    def view(self):
        return GetUserStats.as_view()

    def test_get(self, arf: APIRequestFactory, view):
        kwargs = {"user_string": "5701575", "gamemode": Gamemode.STANDARD}
        url = reverse("user-stats-detail", kwargs=kwargs)
        request = arf.get(
            url,
            data={"user_id_type": "id"},
        )

        response: Response = view(request, **kwargs)

        assert response.status_code == HTTPStatus.OK
        assert response.data["user"]["username"] == "Syrin"
