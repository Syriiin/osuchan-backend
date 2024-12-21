from http import HTTPStatus

import pytest
from django.urls import reverse
from rest_framework.test import force_authenticate

from common.osu.enums import Mods, NewMods
from leaderboards.models import Invite
from users.models import ScoreFilterPreset
from users.views import (
    Me,
    MeInviteList,
    MeScoreFilterPresetDetail,
    MeScoreFilterPresetList,
)


@pytest.fixture
def score_filter_preset(user, score_filter):
    return ScoreFilterPreset.objects.create(
        name="test filter preset",
        user=user,
        score_filter=score_filter,
    )


@pytest.mark.django_db
class TestMe:
    @pytest.fixture
    def view(self):
        return Me.as_view()

    def test_get(self, arf, view, user):
        url = reverse("me")
        request = arf.get(url)

        force_authenticate(request, user)

        response = view(request)

        assert response.status_code == HTTPStatus.OK

    def test_get_unauthenticated(self, arf, view):
        url = reverse("me")
        request = arf.get(url)

        response = view(request)

        assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
class TestMeScoreFilterPresetList:
    @pytest.fixture
    def view(self):
        return MeScoreFilterPresetList.as_view()

    def test_get(self, arf, view, user, score_filter_preset):
        url = reverse("me-score-filter-preset-list")
        request = arf.get(url)

        force_authenticate(request, user)

        response = view(request)

        assert response.status_code == HTTPStatus.OK
        assert len(response.data) == 1

    def test_post(self, arf, view, user):
        url = reverse("me-score-filter-preset-list")
        request = arf.post(
            url,
            data={
                "name": "test sudden death filter",
                "score_filter": {
                    "required_mods": Mods.SUDDEN_DEATH,
                },
            },
            format="json",
        )

        force_authenticate(request, user)

        response = view(request)

        assert response.status_code == HTTPStatus.OK
        assert response.data["name"] == "test sudden death filter"
        assert response.data["score_filter"]["required_mods"] == Mods.SUDDEN_DEATH
        assert response.data["score_filter"]["required_mods_json"] == {
            NewMods.SUDDEN_DEATH: {}
        }


@pytest.mark.django_db
class TestMeScoreFilterPresetDetail:
    @pytest.fixture
    def view(self):
        return MeScoreFilterPresetDetail.as_view()

    def test_get(self, arf, view, user, score_filter_preset):
        kwargs = {"score_filter_preset_id": score_filter_preset.id}
        url = reverse("me-score-filter-preset-detail", kwargs=kwargs)
        request = arf.get(url)

        force_authenticate(request, user)

        response = view(request, **kwargs)

        assert response.status_code == HTTPStatus.OK

    def test_put(self, arf, view, user, score_filter_preset):
        kwargs = {"score_filter_preset_id": score_filter_preset.id}
        url = reverse("me-score-filter-preset-detail", kwargs=kwargs)
        request = arf.put(
            url,
            data={
                "name": "new name",
                "score_filter": {"highest_ar": 8},
            },
            format="json",
        )

        force_authenticate(request, user)

        response = view(request, **kwargs)

        assert response.status_code == HTTPStatus.OK
        assert response.data["name"] == "new name"
        assert response.data["score_filter"]["required_mods"] == Mods.NONE
        assert response.data["score_filter"]["required_mods_json"] == {}
        assert response.data["score_filter"]["highest_ar"] == 8

    def test_delete(self, arf, view, user, score_filter_preset):
        kwargs = {"score_filter_preset_id": score_filter_preset.id}
        url = reverse("me-score-filter-preset-detail", kwargs=kwargs)
        request = arf.delete(url)

        force_authenticate(request, user)

        response = view(request, **kwargs)

        assert response.status_code == HTTPStatus.NO_CONTENT


@pytest.mark.django_db
class TestMeInviteList:
    @pytest.fixture
    def view(self):
        return MeInviteList.as_view()

    @pytest.fixture
    def invite(self, user, osu_user, leaderboard):
        user.osu_user = osu_user
        user.save()
        return Invite.objects.create(leaderboard=leaderboard, user=osu_user)

    def test_get(self, arf, view, user, invite):
        url = reverse("me-invite-list")
        request = arf.get(url)

        force_authenticate(request, user)

        response = view(request)

        assert response.status_code == HTTPStatus.OK
        assert len(response.data) == 1
