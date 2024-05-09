from http import HTTPStatus

import pytest
from django.urls import reverse
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, force_authenticate

from common.osu.enums import Gamemode
from leaderboards.services import create_membership
from profiles.services import refresh_user_from_api
from profiles.views import (
    BeatmapDetail,
    UserMembershipList,
    UserScoreList,
    UserStatsDetail,
)


@pytest.fixture
def stub_user_stats():
    return refresh_user_from_api(user_id=5701575, gamemode=Gamemode.STANDARD)


@pytest.mark.django_db
class TestUserStatsDetail:
    @pytest.fixture
    def view(self):
        return UserStatsDetail.as_view()

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

    def test_get_by_username(self, arf: APIRequestFactory, view):
        kwargs = {"user_string": "syrin", "gamemode": Gamemode.STANDARD}
        url = reverse("user-stats-detail", kwargs=kwargs)
        request = arf.get(
            url,
            data={"user_id_type": "username"},
        )

        response: Response = view(request, **kwargs)

        assert response.status_code == HTTPStatus.OK
        assert response.data["user"]["username"] == "Syrin"


@pytest.mark.django_db
class TestUserScoreList:
    @pytest.fixture
    def view(self):
        return UserScoreList.as_view()

    def test_get(self, arf: APIRequestFactory, view, stub_user_stats):
        kwargs = {"user_id": 5701575, "gamemode": Gamemode.STANDARD}
        url = reverse("user-score-list", kwargs=kwargs)
        request = arf.get(url)

        response: Response = view(request, **kwargs)

        assert response.status_code == HTTPStatus.OK
        assert len(response.data) == 4
        assert response.data[0]["difficulty_total"] == 6.264344677869616
        assert response.data[0]["performance_total"] == 395.281
        assert response.data[0]["nochoke_performance_total"] == 395.39084780089814
        assert response.data[1]["difficulty_total"] == 6.679077669651381
        assert response.data[1]["performance_total"] == 381.606
        assert response.data[1]["nochoke_performance_total"] == 381.60801992603007
        assert response.data[2]["difficulty_total"] == 6.28551550473302
        assert response.data[2]["performance_total"] == 371.204
        assert response.data[2]["nochoke_performance_total"] == 371.203519484766
        assert response.data[3]["difficulty_total"] == 5.5699192504372625
        assert response.data[3]["performance_total"] == 143.53942289330428
        assert response.data[3]["nochoke_performance_total"] == 171.45912084552145

    def test_post(self, arf: APIRequestFactory, view, stub_user_stats, user):
        kwargs = {"user_id": 5701575, "gamemode": Gamemode.STANDARD}
        url = reverse("user-score-list", kwargs=kwargs)
        request = arf.post(url, data={"beatmap_ids": [362949]}, format="json")
        force_authenticate(request, user)

        response: Response = view(request, **kwargs)

        assert response.status_code == HTTPStatus.OK
        assert len(response.data) == 11

    def test_post_unauthenticated(self, arf: APIRequestFactory, view):
        kwargs = {"user_id": 5701575, "gamemode": Gamemode.STANDARD}
        url = reverse("user-score-list", kwargs=kwargs)
        request = arf.post(url, data={"beatmap_ids": [362949]}, format="json")

        response: Response = view(request, **kwargs)

        assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.django_db
class TestUserMembershipList:
    @pytest.fixture
    def view(self):
        return UserMembershipList.as_view()

    @pytest.fixture
    def membership(self, stub_user_stats, leaderboard):
        return create_membership(leaderboard.id, stub_user_stats.user_id)

    def test_get(self, arf: APIRequestFactory, view, membership):
        kwargs = {
            "user_id": 5701575,
            "leaderboard_type": "community",
            "gamemode": Gamemode.STANDARD,
        }
        url = reverse("user-membership-list", kwargs=kwargs)
        request = arf.get(url)

        response: Response = view(request, **kwargs)

        assert response.status_code == HTTPStatus.OK
        assert len(response.data["results"]) == 1


@pytest.mark.django_db
class TestBeatmapDetail:
    @pytest.fixture
    def view(self):
        return BeatmapDetail.as_view()

    def test_get(self, arf: APIRequestFactory, beatmap, view):
        kwargs = {"beatmap_id": beatmap.id}
        url = reverse("beatmap-detail", kwargs=kwargs)
        request = arf.get(url)

        response: Response = view(request, **kwargs)

        assert response.status_code == HTTPStatus.OK
        assert response.data["title"] == beatmap.title
