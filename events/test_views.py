from datetime import datetime, timezone

import pytest
from django.urls import reverse
from rest_framework.test import force_authenticate

from common.osu.enums import Gamemode
from events.enums import BeatmapChallengeType
from events.models import (
    BeatmapChallenge,
    Event,
    EventAttendee,
    EventLeaderboard,
    EventOrganiser,
)
from events.services import create_event_leaderboard, update_attendee_challenge_scores
from events.views import (
    BeatmapChallengeList,
    BeatmapChallengeScoreList,
    EventAttendeeDetail,
    EventAttendeeList,
    EventDetail,
    EventLeaderboardDetail,
    EventLeaderboardList,
    EventList,
)
from leaderboards.enums import LeaderboardAccessType
from leaderboards.models import Leaderboard
from osuauth.models import User
from profiles.enums import AllowedBeatmapStatus, ScoreSet
from profiles.models import OsuUser, Score, ScoreFilter, UserStats


@pytest.fixture
def other_osu_user():
    return OsuUser.objects.create(
        id=999,
        username="OtherUser",
        country="au",
        join_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
        disabled=False,
    )


@pytest.fixture
def other_user(other_osu_user):
    return User.objects.create(username=other_osu_user.id, osu_user=other_osu_user)


@pytest.fixture
def event(osu_user):
    event = Event.objects.create(
        slug="test-event",
        name="Test Event",
        description="",
        logo="",
        theme_colours={"primary": "#ff0000"},
        start_date=datetime(2024, 6, 1, tzinfo=timezone.utc),
        end_date=datetime(2024, 6, 30, tzinfo=timezone.utc),
        creation_time=datetime(2024, 5, 1, tzinfo=timezone.utc),
    )
    EventOrganiser.objects.create(event=event, user=osu_user)
    return event


@pytest.fixture
def event_leaderboard(event, user):
    return create_event_leaderboard(
        event,
        gamemode=Gamemode.STANDARD,
        name="Test Leaderboard",
    )


@pytest.mark.django_db
class TestEventList:
    @pytest.fixture
    def view(self):
        return EventList.as_view()

    def test_get(self, arf, view, event):
        request = arf.get(reverse("event-list"))
        response = view(request)
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["slug"] == event.slug


@pytest.mark.django_db
class TestEventDetail:
    @pytest.fixture
    def view(self):
        return EventDetail.as_view()

    def test_get(self, arf, view, event):
        request = arf.get(reverse("event-detail", kwargs={"slug": event.slug}))
        response = view(request, slug=event.slug)
        assert response.status_code == 200
        assert response.data["slug"] == event.slug

    def test_get_not_found(self, arf, view):
        request = arf.get(reverse("event-detail", kwargs={"slug": "nonexistent"}))
        response = view(request, slug="nonexistent")
        assert response.status_code == 404

    def test_patch(self, arf, view, event, user):
        request = arf.patch(
            reverse("event-detail", kwargs={"slug": event.slug}),
            data={"name": "Updated Event"},
            format="json",
        )
        force_authenticate(request, user)
        response = view(request, slug=event.slug)
        assert response.status_code == 200
        assert response.data["name"] == "Updated Event"

    def test_patch_unauthenticated(self, arf, view, event):
        request = arf.patch(
            reverse("event-detail", kwargs={"slug": event.slug}),
            data={"name": "Updated Event"},
            format="json",
        )
        response = view(request, slug=event.slug)
        assert response.status_code == 403

    def test_patch_not_organiser(self, arf, view, event, other_user):
        request = arf.patch(
            reverse("event-detail", kwargs={"slug": event.slug}),
            data={"name": "Updated Event"},
            format="json",
        )
        force_authenticate(request, other_user)
        response = view(request, slug=event.slug)
        assert response.status_code == 403

    def test_patch_dates_cascade_to_score_filters(
        self, arf, view, event, event_leaderboard, user
    ):
        new_start = datetime(2024, 7, 1, tzinfo=timezone.utc)
        new_end = datetime(2024, 7, 31, tzinfo=timezone.utc)
        request = arf.patch(
            reverse("event-detail", kwargs={"slug": event.slug}),
            data={
                "start_date": new_start.isoformat(),
                "end_date": new_end.isoformat(),
            },
            format="json",
        )
        force_authenticate(request, user)
        response = view(request, slug=event.slug)
        assert response.status_code == 200

        event_leaderboard.leaderboard.score_filter.refresh_from_db()
        assert event_leaderboard.leaderboard.score_filter.oldest_score_date == new_start
        assert event_leaderboard.leaderboard.score_filter.newest_score_date == new_end


@pytest.mark.django_db
class TestEventAttendeeList:
    @pytest.fixture
    def view(self):
        return EventAttendeeList.as_view()

    def test_get(self, arf, view, event):
        request = arf.get(reverse("event-attendee-list", kwargs={"slug": event.slug}))
        response = view(request, slug=event.slug)
        assert response.status_code == 200
        assert response.data["count"] == 0
        assert response.data["results"] == []

    def test_post(self, arf, view, event, user):
        request = arf.post(
            reverse("event-attendee-list", kwargs={"slug": event.slug}),
            data={"user_id": user.osu_user.id},
            format="json",
        )
        force_authenticate(request, user)
        response = view(request, slug=event.slug)
        assert response.status_code == 201
        assert EventAttendee.objects.filter(
            event=event, user_id=user.osu_user.id
        ).exists()

    def test_post_unauthenticated(self, arf, view, event):
        request = arf.post(
            reverse("event-attendee-list", kwargs={"slug": event.slug}),
            data={"user_id": 1},
            format="json",
        )
        response = view(request, slug=event.slug)
        assert response.status_code == 403

    def test_post_not_organiser(self, arf, view, event, other_user):
        request = arf.post(
            reverse("event-attendee-list", kwargs={"slug": event.slug}),
            data={"user_id": other_user.osu_user.id},
            format="json",
        )
        force_authenticate(request, other_user)
        response = view(request, slug=event.slug)
        assert response.status_code == 403

    def test_post_missing_user_id(self, arf, view, event, user):
        request = arf.post(
            reverse("event-attendee-list", kwargs={"slug": event.slug}),
            data={},
            format="json",
        )
        force_authenticate(request, user)
        response = view(request, slug=event.slug)
        assert response.status_code == 400

    def test_post_user_not_found(self, arf, view, event, user):
        request = arf.post(
            reverse("event-attendee-list", kwargs={"slug": event.slug}),
            data={"user_id": 999999},
            format="json",
        )
        force_authenticate(request, user)
        response = view(request, slug=event.slug)
        assert response.status_code == 404


@pytest.mark.django_db
class TestEventAttendeeDetail:
    def test_delete(self, arf, event, user):
        EventAttendee.objects.create(event=event, user_id=user.osu_user.id)
        view = EventAttendeeDetail.as_view()
        request = arf.delete(
            reverse(
                "event-attendee-detail",
                kwargs={"slug": event.slug, "user_id": user.osu_user.id},
            )
        )
        force_authenticate(request, user)
        response = view(request, slug=event.slug, user_id=user.osu_user.id)
        assert response.status_code == 204
        assert not EventAttendee.objects.filter(
            event=event, user_id=user.osu_user.id
        ).exists()

    def test_delete_unauthenticated(self, arf, event, user):
        EventAttendee.objects.create(event=event, user_id=user.osu_user.id)
        view = EventAttendeeDetail.as_view()
        request = arf.delete(
            reverse(
                "event-attendee-detail",
                kwargs={"slug": event.slug, "user_id": user.osu_user.id},
            )
        )
        response = view(request, slug=event.slug, user_id=user.osu_user.id)
        assert response.status_code == 403

    def test_delete_not_organiser(self, arf, event, user, other_user):
        EventAttendee.objects.create(event=event, user_id=user.osu_user.id)
        view = EventAttendeeDetail.as_view()
        request = arf.delete(
            reverse(
                "event-attendee-detail",
                kwargs={"slug": event.slug, "user_id": user.osu_user.id},
            )
        )
        force_authenticate(request, other_user)
        response = view(request, slug=event.slug, user_id=user.osu_user.id)
        assert response.status_code == 403


@pytest.mark.django_db
class TestEventLeaderboardList:
    @pytest.fixture
    def view(self):
        return EventLeaderboardList.as_view()

    def test_get(self, arf, view, event):
        request = arf.get(
            reverse("event-leaderboard-list", kwargs={"slug": event.slug})
        )
        response = view(request, slug=event.slug)
        assert response.status_code == 200
        assert len(response.data) == 0

    def test_post(self, arf, view, event, user):
        request = arf.post(
            reverse("event-leaderboard-list", kwargs={"slug": event.slug}),
            data={
                "gamemode": Gamemode.STANDARD,
                "name": "Test Leaderboard",
            },
            format="json",
        )
        force_authenticate(request, user)
        response = view(request, slug=event.slug)
        assert response.status_code == 201

        event_leaderboard = EventLeaderboard.objects.get(event=event)
        # event_leaderboard.leaderboard.score_filter.refresh_from_db()
        assert event_leaderboard.leaderboard.is_event is True
        assert event_leaderboard.leaderboard.owner is None
        assert (
            event_leaderboard.leaderboard.access_type
            == LeaderboardAccessType.PUBLIC_INVITE_ONLY
        )
        assert event_leaderboard.leaderboard.custom_colours == event.theme_colours
        assert event_leaderboard.leaderboard.icon_url == event.logo
        assert event_leaderboard.leaderboard.score_set == ScoreSet.NORMAL
        assert (
            event_leaderboard.leaderboard.score_filter.allowed_beatmap_status
            == AllowedBeatmapStatus.RANKED_ONLY
        )
        assert (
            event_leaderboard.leaderboard.score_filter.oldest_score_date
            == event.start_date
        )
        assert (
            event_leaderboard.leaderboard.score_filter.newest_score_date
            == event.end_date
        )

    def test_post_unauthenticated(self, arf, view, event):
        request = arf.post(
            reverse("event-leaderboard-list", kwargs={"slug": event.slug}),
            data={
                "gamemode": Gamemode.STANDARD,
                "name": "Test Leaderboard",
            },
            format="json",
        )
        response = view(request, slug=event.slug)
        assert response.status_code == 403

    def test_post_not_organiser(self, arf, view, event, other_user):
        request = arf.post(
            reverse("event-leaderboard-list", kwargs={"slug": event.slug}),
            data={
                "gamemode": Gamemode.STANDARD,
                "name": "Test Leaderboard",
            },
            format="json",
        )
        force_authenticate(request, other_user)
        response = view(request, slug=event.slug)
        assert response.status_code == 403


@pytest.mark.django_db
class TestEventLeaderboardDetail:
    def test_delete(self, arf, event_leaderboard, user):
        view = EventLeaderboardDetail.as_view()
        request = arf.delete(
            reverse(
                "event-leaderboard-detail",
                kwargs={
                    "slug": event_leaderboard.event.slug,
                    "event_leaderboard_id": event_leaderboard.id,
                },
            )
        )
        force_authenticate(request, user)
        response = view(
            request,
            slug=event_leaderboard.event.slug,
            event_leaderboard_id=event_leaderboard.id,
        )
        assert response.status_code == 204
        assert not EventLeaderboard.objects.filter(id=event_leaderboard.id).exists()
        assert not Leaderboard.objects.filter(
            id=event_leaderboard.leaderboard_id
        ).exists()
        assert not ScoreFilter.objects.filter(
            id=event_leaderboard.leaderboard.score_filter_id
        ).exists()

    def test_delete_unauthenticated(self, arf, event_leaderboard):
        view = EventLeaderboardDetail.as_view()
        request = arf.delete(
            reverse(
                "event-leaderboard-detail",
                kwargs={
                    "slug": event_leaderboard.event.slug,
                    "event_leaderboard_id": event_leaderboard.id,
                },
            )
        )
        response = view(
            request,
            slug=event_leaderboard.event.slug,
            event_leaderboard_id=event_leaderboard.id,
        )
        assert response.status_code == 403

    def test_delete_not_organiser(self, arf, event_leaderboard, other_user):
        view = EventLeaderboardDetail.as_view()
        request = arf.delete(
            reverse(
                "event-leaderboard-detail",
                kwargs={
                    "slug": event_leaderboard.event.slug,
                    "event_leaderboard_id": event_leaderboard.id,
                },
            )
        )
        force_authenticate(request, other_user)
        response = view(
            request,
            slug=event_leaderboard.event.slug,
            event_leaderboard_id=event_leaderboard.id,
        )
        assert response.status_code == 403


def _create_score(user_stats, beatmap, best_combo, count_miss, date):
    return Score.objects.create(
        score=1000000,
        count_300=1000,
        count_100=0,
        count_50=0,
        count_miss=count_miss,
        count_geki=0,
        count_katu=0,
        statistics={"great": 1000, "ok": 0, "meh": 0, "miss": count_miss},
        best_combo=best_combo,
        perfect=False,
        mods=0,
        mods_json={},
        is_stable=True,
        rank="S",
        date=date,
        beatmap=beatmap,
        user_stats=user_stats,
        gamemode=Gamemode.STANDARD,
        accuracy=100.0,
        bpm=180,
        length=368,
        circle_size=4,
        approach_rate=9.7,
        overall_difficulty=8.4,
        result=0,
        mutation=0,
    )


@pytest.fixture
def other_user_stats(other_osu_user):
    return UserStats.objects.create(
        gamemode=Gamemode.STANDARD,
        playcount=1000,
        playtime=100000,
        level=50,
        ranked_score=1000000,
        total_score=5000000,
        rank=50000,
        country_rank=2000,
        pp=2000,
        accuracy=95.0,
        count_300=5000,
        count_100=500,
        count_50=50,
        count_rank_ss=10,
        count_rank_ssh=5,
        count_rank_s=100,
        count_rank_sh=50,
        count_rank_a=200,
        extra_pp=0,
        score_style_accuracy=0,
        score_style_bpm=0,
        score_style_cs=0,
        score_style_ar=0,
        score_style_od=0,
        score_style_length=0,
        user=other_osu_user,
        last_updated=datetime(2025, 7, 14, tzinfo=timezone.utc),
    )


@pytest.fixture
def beatmap_challenge(event, beatmap):
    return BeatmapChallenge.objects.create(
        description="$100 USD bounty for first FC",
        gamemode=Gamemode.STANDARD,
        challenge_type=BeatmapChallengeType.BEST_COMBO,
        event=event,
        beatmap=beatmap,
    )


@pytest.mark.django_db
class TestBeatmapChallengeList:
    @pytest.fixture
    def view(self):
        return BeatmapChallengeList.as_view()

    def test_get(self, arf, view, event, beatmap_challenge):
        request = arf.get(
            reverse("beatmap-challenge-list", kwargs={"slug": event.slug})
        )
        response = view(request, slug=event.slug)
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["description"] == beatmap_challenge.description
        assert response.data[0]["beatmap"]["id"] == beatmap_challenge.beatmap_id

    def test_get_empty(self, arf, view, event):
        request = arf.get(
            reverse("beatmap-challenge-list", kwargs={"slug": event.slug})
        )
        response = view(request, slug=event.slug)
        assert response.status_code == 200
        assert response.data == []

    def test_get_event_not_found(self, arf, view):
        request = arf.get(
            reverse("beatmap-challenge-list", kwargs={"slug": "nonexistent"})
        )
        response = view(request, slug="nonexistent")
        assert response.status_code == 404


@pytest.mark.django_db
class TestBeatmapChallengeScoreList:
    @pytest.fixture
    def view(self):
        return BeatmapChallengeScoreList.as_view()

    def test_get(self, arf, view, event, beatmap_challenge, user, user_stats, beatmap):
        EventAttendee.objects.create(event=event, user_id=user.osu_user.id)
        _create_score(
            user_stats,
            beatmap,
            best_combo=2757,
            count_miss=0,
            date=datetime(2024, 6, 15, tzinfo=timezone.utc),
        )
        update_attendee_challenge_scores(beatmap_challenge, user.osu_user.id)

        request = arf.get(
            reverse(
                "beatmap-challenge-score-list",
                kwargs={"slug": event.slug, "challenge_id": beatmap_challenge.id},
            )
        )
        response = view(request, slug=event.slug, challenge_id=beatmap_challenge.id)
        assert response.status_code == 200
        assert len(response.data) == 1

    def test_get_event_not_found(self, arf, view, beatmap_challenge):
        request = arf.get(
            reverse(
                "beatmap-challenge-score-list",
                kwargs={"slug": "nonexistent", "challenge_id": beatmap_challenge.id},
            )
        )
        response = view(request, slug="nonexistent", challenge_id=beatmap_challenge.id)
        assert response.status_code == 404

    def test_get_challenge_not_found(self, arf, view, event):
        request = arf.get(
            reverse(
                "beatmap-challenge-score-list",
                kwargs={"slug": event.slug, "challenge_id": 999},
            )
        )
        response = view(request, slug=event.slug, challenge_id=999)
        assert response.status_code == 404

    def test_order_best_combo(
        self, arf, view, event, beatmap_challenge, user, user_stats, beatmap
    ):
        EventAttendee.objects.create(event=event, user_id=user.osu_user.id)

        _create_score(
            user_stats,
            beatmap,
            best_combo=2000,
            count_miss=0,
            date=datetime(2024, 6, 10, tzinfo=timezone.utc),
        )
        _create_score(
            user_stats,
            beatmap,
            best_combo=2500,
            count_miss=0,
            date=datetime(2024, 6, 11, tzinfo=timezone.utc),
        )
        best = _create_score(
            user_stats,
            beatmap,
            best_combo=2500,
            count_miss=0,
            date=datetime(2024, 6, 9, tzinfo=timezone.utc),
        )

        update_attendee_challenge_scores(beatmap_challenge, user.osu_user.id)

        request = arf.get(
            reverse(
                "beatmap-challenge-score-list",
                kwargs={"slug": event.slug, "challenge_id": beatmap_challenge.id},
            )
        )
        response = view(request, slug=event.slug, challenge_id=beatmap_challenge.id)
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["id"] == best.id

    def test_order_lowest_miss_count(self, arf, view, user, user_stats, beatmap, event):
        challenge = BeatmapChallenge.objects.create(
            description="Zero misses challenge",
            gamemode=Gamemode.STANDARD,
            challenge_type=BeatmapChallengeType.LOWEST_MISS_COUNT,
            event=event,
            beatmap=beatmap,
        )
        EventAttendee.objects.create(event=event, user_id=user.osu_user.id)

        _create_score(
            user_stats,
            beatmap,
            best_combo=2800,
            count_miss=2,
            date=datetime(2024, 6, 10, tzinfo=timezone.utc),
        )
        _create_score(
            user_stats,
            beatmap,
            best_combo=2700,
            count_miss=0,
            date=datetime(2024, 6, 12, tzinfo=timezone.utc),
        )
        best = _create_score(
            user_stats,
            beatmap,
            best_combo=2600,
            count_miss=0,
            date=datetime(2024, 6, 9, tzinfo=timezone.utc),
        )

        update_attendee_challenge_scores(challenge, user.osu_user.id)

        request = arf.get(
            reverse(
                "beatmap-challenge-score-list",
                kwargs={"slug": event.slug, "challenge_id": challenge.id},
            )
        )
        response = view(request, slug=event.slug, challenge_id=challenge.id)
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["id"] == best.id

    def test_get_limit(
        self,
        arf,
        view,
        event,
        beatmap_challenge,
        user,
        other_user,
        user_stats,
        beatmap,
        other_user_stats,
    ):
        EventAttendee.objects.create(event=event, user_id=user.osu_user.id)
        EventAttendee.objects.create(event=event, user_id=other_user.osu_user.id)

        for u_stats, usr in [(user_stats, user), (other_user_stats, other_user)]:
            _create_score(
                u_stats,
                beatmap,
                best_combo=2000,
                count_miss=0,
                date=datetime(2024, 6, 10, tzinfo=timezone.utc),
            )
            update_attendee_challenge_scores(beatmap_challenge, usr.osu_user.id)

        request = arf.get(
            reverse(
                "beatmap-challenge-score-list",
                kwargs={"slug": event.slug, "challenge_id": beatmap_challenge.id},
            )
            + "?limit=1"
        )
        response = view(request, slug=event.slug, challenge_id=beatmap_challenge.id)
        assert response.status_code == 200
        assert len(response.data) == 1
