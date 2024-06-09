from http import HTTPStatus

import pytest
from django.urls import reverse
from rest_framework.test import force_authenticate

from common.osu.enums import Gamemode
from leaderboards.enums import LeaderboardAccessType
from leaderboards.views import (
    LeaderboardBeatmapScoreList,
    LeaderboardDetail,
    LeaderboardInviteDetail,
    LeaderboardInviteList,
    LeaderboardList,
    LeaderboardMemberDetail,
    LeaderboardMemberList,
    LeaderboardMemberScoreList,
    LeaderboardScoreList,
)
from profiles.enums import ScoreSet


@pytest.mark.django_db
class TestLeaderboardList:
    @pytest.fixture
    def view(self):
        return LeaderboardList.as_view()

    def test_get(self, arf, view, leaderboard):
        kwargs = {"leaderboard_type": "community", "gamemode": Gamemode.STANDARD}
        url = reverse("leaderboard-list", kwargs=kwargs)
        request = arf.get(url)

        response = view(request, **kwargs)

        assert response.status_code == HTTPStatus.OK
        assert len(response.data["results"]) == 1

    def test_post(self, arf, view, user):
        kwargs = {"leaderboard_type": "community", "gamemode": Gamemode.STANDARD}
        url = reverse("leaderboard-list", kwargs=kwargs)
        request = arf.post(
            url,
            data={
                "score_set": ScoreSet.NORMAL,
                "access_type": LeaderboardAccessType.PUBLIC,
                "name": "test leaderboard",
                "description": "this is a test leaderboard",
                "icon_url": "",
                "score_filter": {"lowest_length": 90},
                "allow_past_scores": True,
            },
            format="json",
        )

        force_authenticate(request, user)

        response = view(request, **kwargs)

        assert response.status_code == HTTPStatus.OK
        assert response.data["name"] == "test leaderboard"
        assert response.data["score_filter"]["lowest_length"] == 90


@pytest.mark.django_db
class TestLeaderboardDetail:
    @pytest.fixture
    def view(self):
        return LeaderboardDetail.as_view()

    def test_get(self, arf, view, leaderboard):
        kwargs = {
            "leaderboard_type": "community",
            "gamemode": Gamemode.STANDARD,
            "leaderboard_id": leaderboard.id,
        }
        url = reverse("leaderboard-detail", kwargs=kwargs)
        request = arf.get(url)

        response = view(request, **kwargs)

        assert response.status_code == HTTPStatus.OK

    def test_delete(self, arf, view, leaderboard):
        kwargs = {
            "leaderboard_type": "community",
            "gamemode": Gamemode.STANDARD,
            "leaderboard_id": leaderboard.id,
        }
        url = reverse("leaderboard-detail", kwargs=kwargs)
        request = arf.delete(url)

        force_authenticate(request, leaderboard.owner.user)

        response = view(request, **kwargs)

        assert response.status_code == HTTPStatus.NO_CONTENT

    def test_patch(self, arf, view, leaderboard):
        kwargs = {
            "leaderboard_type": "community",
            "gamemode": Gamemode.STANDARD,
            "leaderboard_id": leaderboard.id,
        }
        url = reverse("leaderboard-detail", kwargs=kwargs)
        request = arf.patch(
            url,
            data={"name": "new name"},
            format="json",
        )

        force_authenticate(request, leaderboard.owner.user)

        response = view(request, **kwargs)

        assert response.status_code == HTTPStatus.OK
        assert response.data["name"] == "new name"


@pytest.mark.django_db
class TestLeaderboardScoreList:
    @pytest.fixture
    def view(self):
        return LeaderboardScoreList.as_view()

    def test_get(self, arf, view, leaderboard):
        # TODO: make this test actually return data
        kwargs = {
            "leaderboard_type": "community",
            "gamemode": Gamemode.STANDARD,
            "leaderboard_id": leaderboard.id,
        }
        url = reverse("leaderboard-score-list", kwargs=kwargs)
        request = arf.get(url)

        response = view(request, **kwargs)

        assert response.status_code == HTTPStatus.OK
        assert len(response.data) == 0


@pytest.mark.django_db
class TestLeaderboardMemberList:
    @pytest.fixture
    def view(self):
        return LeaderboardMemberList.as_view()

    def test_get(self, arf, view, leaderboard, membership):
        kwargs = {
            "leaderboard_type": "community",
            "gamemode": Gamemode.STANDARD,
            "leaderboard_id": leaderboard.id,
        }
        url = reverse("leaderboard-member-list", kwargs=kwargs)
        request = arf.get(url)

        response = view(request, **kwargs)

        assert response.status_code == HTTPStatus.OK
        assert len(response.data) == 2

    def test_post(self, arf, view, leaderboard, user):
        kwargs = {
            "leaderboard_type": "community",
            "gamemode": Gamemode.STANDARD,
            "leaderboard_id": leaderboard.id,
        }
        url = reverse("leaderboard-member-list", kwargs=kwargs)
        request = arf.post(url, data={}, format="json")

        force_authenticate(request, user)

        response = view(request, **kwargs)

        assert response.status_code == HTTPStatus.OK
        assert response.data["user"]["username"] == "TestOsuUser"


@pytest.mark.django_db
class TestLeaderboardMemberDetail:
    @pytest.fixture
    def view(self):
        return LeaderboardMemberDetail.as_view()

    def test_get(self, arf, view, membership):
        kwargs = {
            "leaderboard_type": "community",
            "gamemode": Gamemode.STANDARD,
            "leaderboard_id": membership.leaderboard_id,
            "user_id": membership.user_id,
        }
        url = reverse("leaderboard-member-detail", kwargs=kwargs)
        request = arf.get(url)

        response = view(request, **kwargs)

        assert response.status_code == HTTPStatus.OK
        assert response.data["user"]["username"] == "TestOsuUser"

    def test_delete(self, arf, view, membership):
        kwargs = {
            "leaderboard_type": "community",
            "gamemode": Gamemode.STANDARD,
            "leaderboard_id": membership.leaderboard_id,
            "user_id": membership.user_id,
        }
        url = reverse("leaderboard-member-detail", kwargs=kwargs)
        request = arf.delete(url)

        force_authenticate(request, membership.user.user)

        response = view(request, **kwargs)

        assert response.status_code == HTTPStatus.NO_CONTENT


@pytest.mark.django_db
class TestLeaderboardInviteList:
    @pytest.fixture
    def view(self):
        return LeaderboardInviteList.as_view()

    def test_get(self, arf, view, invite):
        kwargs = {
            "leaderboard_type": "community",
            "gamemode": Gamemode.STANDARD,
            "leaderboard_id": invite.leaderboard_id,
        }
        url = reverse("leaderboard-invite-list", kwargs=kwargs)
        request = arf.get(url)

        force_authenticate(request, invite.leaderboard.owner.user)

        response = view(request, **kwargs)

        assert response.status_code == HTTPStatus.OK
        assert len(response.data) == 1

    def test_post(self, arf, view, leaderboard, osu_user):
        kwargs = {
            "leaderboard_type": "community",
            "gamemode": Gamemode.STANDARD,
            "leaderboard_id": leaderboard.id,
        }
        url = reverse("leaderboard-invite-list", kwargs=kwargs)
        request = arf.post(
            url,
            data={"user_ids": [5701575], "message": "test message"},
            format="json",
        )

        force_authenticate(request, leaderboard.owner.user)

        response = view(request, **kwargs)

        assert response.status_code == HTTPStatus.OK
        assert len(response.data) == 1


@pytest.mark.django_db
class TestLeaderboardInviteDetail:
    @pytest.fixture
    def view(self):
        return LeaderboardInviteDetail.as_view()

    def test_get(self, arf, view, invite):
        kwargs = {
            "leaderboard_type": "community",
            "gamemode": Gamemode.STANDARD,
            "leaderboard_id": invite.leaderboard_id,
            "user_id": invite.user_id,
        }
        url = reverse("leaderboard-invite-detail", kwargs=kwargs)
        request = arf.get(url)

        force_authenticate(request, invite.user.user)

        response = view(request, **kwargs)

        assert response.status_code == HTTPStatus.OK
        assert response.data["message"] == "test invite message"
        assert response.data["user"]["username"] == "TestOsuUser"

    def test_delete(self, arf, view, invite):
        kwargs = {
            "leaderboard_type": "community",
            "gamemode": Gamemode.STANDARD,
            "leaderboard_id": invite.leaderboard_id,
            "user_id": invite.user_id,
        }
        url = reverse("leaderboard-invite-detail", kwargs=kwargs)
        request = arf.delete(url)

        force_authenticate(request, invite.user.user)

        response = view(request, **kwargs)

        assert response.status_code == HTTPStatus.NO_CONTENT


@pytest.mark.django_db
class TestLeaderboardBeatmapScoreList:
    @pytest.fixture
    def view(self):
        return LeaderboardBeatmapScoreList.as_view()

    def test_get(self, arf, view, leaderboard):
        # TODO: actually return data
        kwargs = {
            "leaderboard_type": "community",
            "gamemode": Gamemode.STANDARD,
            "leaderboard_id": leaderboard.id,
            "beatmap_id": 1,
        }
        url = reverse("leaderboard-beatmap-score-list", kwargs=kwargs)
        request = arf.get(url)

        response = view(request, **kwargs)

        assert response.status_code == HTTPStatus.OK
        assert len(response.data) == 0


@pytest.mark.django_db
class TestLeaderboardMemberScoreList:
    @pytest.fixture
    def view(self):
        return LeaderboardMemberScoreList.as_view()

    def test_get(self, arf, view, membership):
        # TODO: actually return data
        kwargs = {
            "leaderboard_type": "community",
            "gamemode": Gamemode.STANDARD,
            "leaderboard_id": membership.leaderboard_id,
            "user_id": membership.user_id,
        }
        url = reverse("leaderboard-member-score-list", kwargs=kwargs)
        request = arf.get(url)

        response = view(request, **kwargs)

        assert response.status_code == HTTPStatus.OK
        assert len(response.data) == 0
