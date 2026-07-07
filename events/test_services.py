from datetime import datetime, timezone

import pytest

from common.osu.enums import Gamemode
from events.models import Event, EventAttendee, EventLeaderboard, EventOrganiser
from events.services import (
    add_event_attendee,
    create_event_leaderboard,
    delete_event_leaderboard,
    remove_event_attendee,
    update_event,
)
from leaderboards.enums import LeaderboardAccessType
from leaderboards.models import Leaderboard, Membership
from profiles.enums import AllowedBeatmapStatus, ScoreSet
from profiles.models import ScoreFilter


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
def event_with_leaderboard(event, user):
    return create_event_leaderboard(
        event,
        gamemode=Gamemode.STANDARD,
        name="Test Leaderboard",
    )


@pytest.mark.django_db
class TestEventServices:
    def test_update_event(self, event):
        updated = update_event(event, name="New Name")
        updated.refresh_from_db()

        assert updated.name == "New Name"

    def test_date_updates_cascade_to_score_filters(self, event_with_leaderboard):
        event = event_with_leaderboard.event
        new_start = datetime(2024, 6, 15, tzinfo=timezone.utc)
        update_event(event, start_date=new_start)
        event_with_leaderboard.leaderboard.score_filter.refresh_from_db()

        assert (
            event_with_leaderboard.leaderboard.score_filter.oldest_score_date
            == new_start
        )

    def test_non_date_updates_dont_cascade_to_score_filters(
        self, event_with_leaderboard
    ):
        event = event_with_leaderboard.event
        original_start = (
            event_with_leaderboard.leaderboard.score_filter.oldest_score_date
        )
        update_event(event, name="Just a rename")
        event_with_leaderboard.leaderboard.score_filter.refresh_from_db()

        assert (
            event_with_leaderboard.leaderboard.score_filter.oldest_score_date
            == original_start
        )

    def test_add_player(self, event_with_leaderboard, user):
        event = event_with_leaderboard.event
        player, created = add_event_attendee(event, user.osu_user.id)

        assert created is True
        assert player.user_id == user.osu_user.id
        assert Membership.objects.filter(
            leaderboard__event_leaderboard__event=event,
            user_id=user.osu_user.id,
        ).exists()

    def test_remove_player(self, event_with_leaderboard, user):
        event = event_with_leaderboard.event
        add_event_attendee(event, user.osu_user.id)
        remove_event_attendee(event, user.osu_user.id)

        assert not EventAttendee.objects.filter(
            event=event, user_id=user.osu_user.id
        ).exists()
        assert not Membership.objects.filter(
            leaderboard=event_with_leaderboard.leaderboard_id,
            user_id=user.osu_user.id,
        ).exists()


@pytest.mark.django_db
class TestEventLeaderboardServices:
    def test_create_event_leaderboard(self, event, user):
        EventAttendee.objects.create(event=event, user_id=user.osu_user.id)
        event_leaderboard = create_event_leaderboard(
            event,
            gamemode=Gamemode.STANDARD,
            name="Test Leaderboard",
        )

        assert event_leaderboard.event == event

        leaderboard = event_leaderboard.leaderboard
        assert leaderboard.is_event is True
        assert leaderboard.owner is None
        assert leaderboard.access_type == LeaderboardAccessType.PUBLIC
        assert leaderboard.custom_colours == event.theme_colours
        assert leaderboard.icon_url == event.logo
        assert leaderboard.score_set == ScoreSet.NORMAL

        score_filter = leaderboard.score_filter
        assert score_filter.allowed_beatmap_status == AllowedBeatmapStatus.RANKED_ONLY
        assert score_filter.oldest_score_date == event.start_date
        assert score_filter.newest_score_date == event.end_date

        assert Membership.objects.filter(
            leaderboard=leaderboard.id, user_id=user.osu_user.id
        ).exists()

    def test_delete_event_leaderboard(self, event_with_leaderboard):
        event_leaderboard = event_with_leaderboard
        leaderboard_id = event_leaderboard.leaderboard.id
        score_filter_id = event_leaderboard.leaderboard.score_filter.id

        delete_event_leaderboard(event_leaderboard)

        assert not EventLeaderboard.objects.filter(id=event_leaderboard.id).exists()
        assert not Leaderboard.objects.filter(id=leaderboard_id).exists()
        assert not ScoreFilter.objects.filter(id=score_filter_id).exists()
