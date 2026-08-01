from datetime import datetime, timezone

import pytest

from common.osu.difficultycalculator import get_default_difficulty_calculator_class
from common.osu.enums import Gamemode
from events.models import Event, EventAttendee, EventLeaderboard, EventOrganiser
from events.services import (
    add_event_attendee,
    create_event_leaderboard,
    delete_event_leaderboard,
    recalculate_event_stats,
    remove_event_attendee,
    update_event,
)
from leaderboards.enums import LeaderboardAccessType
from leaderboards.models import Leaderboard, Membership
from profiles.enums import AllowedBeatmapStatus, ScoreMutation, ScoreSet
from profiles.models import (
    Beatmap,
    DifficultyCalculation,
    OsuUser,
    PerformanceCalculation,
    PerformanceValue,
    Score,
    ScoreFilter,
    UserStats,
)


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
        assert leaderboard.access_type == LeaderboardAccessType.PUBLIC_INVITE_ONLY
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


def create_user_stats(
    user_id: int, gamemode: Gamemode = Gamemode.STANDARD
) -> UserStats:
    return UserStats.objects.create(
        gamemode=gamemode,
        playcount=0,
        playtime=0,
        level=0,
        ranked_score=0,
        total_score=0,
        rank=0,
        country_rank=0,
        pp=0,
        accuracy=0,
        count_300=0,
        count_100=0,
        count_50=0,
        count_rank_ss=0,
        count_rank_ssh=0,
        count_rank_s=0,
        count_rank_sh=0,
        count_rank_a=0,
        user_id=user_id,
        last_updated=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )


def get_statistics(
    gamemode: Gamemode,
    count_300: int,
    count_100: int,
    count_50: int,
    count_geki: int = 0,
    count_katu: int = 0,
) -> dict:
    if gamemode == Gamemode.STANDARD:
        return {"great": count_300, "ok": count_100, "meh": count_50, "miss": 0}
    if gamemode == Gamemode.TAIKO:
        return {"great": count_300, "ok": count_100, "miss": 0}
    if gamemode == Gamemode.CATCH:
        return {
            "great": count_300,
            "large_tick_hit": count_100,
            "small_tick_hit": count_50,
            "miss": 0,
        }
    if gamemode == Gamemode.MANIA:
        return {
            "perfect": count_geki,
            "great": count_300,
            "good": count_katu,
            "ok": count_100,
            "meh": count_50,
            "miss": 0,
        }
    raise ValueError(f"{gamemode} is not a valid gamemode")


def create_score_with_performance(
    user_stats: UserStats,
    beatmap: Beatmap,
    gamemode: Gamemode,
    date: datetime,
    count_300: int = 0,
    count_100: int = 0,
    count_50: int = 0,
    count_geki: int = 0,
    count_katu: int = 0,
    length: float = 0.0,
    pp: float = 0.0,
    mutation: int = ScoreMutation.NONE,
) -> Score:
    engine = get_default_difficulty_calculator_class(gamemode).engine()
    statistics = get_statistics(
        gamemode, count_300, count_100, count_50, count_geki, count_katu
    )
    score = Score.objects.create(
        score=0,
        count_300=count_300,
        count_100=count_100,
        count_50=count_50,
        count_miss=0,
        count_geki=count_geki,
        count_katu=count_katu,
        statistics=statistics,
        best_combo=0,
        perfect=False,
        mods=0,
        mods_json={},
        is_stable=False,
        rank="A",
        date=date,
        beatmap=beatmap,
        user_stats=user_stats,
        gamemode=gamemode,
        accuracy=100,
        bpm=0,
        length=length,
        circle_size=0,
        approach_rate=0,
        overall_difficulty=0,
        mutation=mutation,
    )
    difficulty_calculation, _ = DifficultyCalculation.objects.get_or_create(
        beatmap=beatmap,
        mods=0,
        calculator_engine=engine,
        defaults={"calculator_version": "v1"},
    )
    calculation = PerformanceCalculation.objects.create(
        score=score,
        difficulty_calculation=difficulty_calculation,
        calculator_engine=engine,
        calculator_version="v1",
    )
    PerformanceValue.objects.create(calculation=calculation, name="total", value=pp)
    return score


@pytest.mark.django_db
class TestEventStats:
    @pytest.fixture
    def stats_event(self, event, user):
        EventAttendee.objects.create(event=event, user_id=user.osu_user.id)
        return event

    def test_recalculate_event_stats(self, stats_event, user, user_stats, beatmap):
        other_user = OsuUser.objects.create(
            id=2,
            username="OtherUser",
            country="us",
            join_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            disabled=False,
        )
        EventAttendee.objects.create(event=stats_event, user_id=other_user.id)
        other_user_stats = create_user_stats(other_user.id)
        other_beatmap = Beatmap.objects.create(
            id=2,
            set_id=2,
            artist="another artist",
            title="another title",
            difficulty_name="another difficulty",
            gamemode=Gamemode.STANDARD,
            status=1,
            creator_name="test creator",
            bpm=180,
            drain_time=556,
            total_time=682,
            max_combo=2843,
            circle_size=4,
            overall_difficulty=6,
            approach_rate=8,
            health_drain=5,
            submission_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            approval_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            last_updated=datetime(2023, 1, 1, tzinfo=timezone.utc),
            hitobject_counts={},
            creator_id=1,
        )

        date = datetime(2024, 6, 10, tzinfo=timezone.utc)
        create_score_with_performance(
            user_stats,
            beatmap,
            Gamemode.STANDARD,
            date,
            count_300=100,
            count_100=20,
            count_50=5,
            length=100.0,
            pp=50.5,
        )
        create_score_with_performance(
            user_stats,
            other_beatmap,
            Gamemode.STANDARD,
            datetime(2024, 6, 11, tzinfo=timezone.utc),
            count_300=200,
            count_100=10,
            count_50=0,
            length=200.0,
            pp=80.0,
        )
        create_score_with_performance(
            other_user_stats,
            other_beatmap,
            Gamemode.STANDARD,
            date,
            count_300=300,
            count_100=30,
            count_50=1,
            length=300.0,
            pp=60.0,
        )

        stats = recalculate_event_stats(stats_event)

        assert stats.total_scores == 3
        assert stats.total_regular_hits == 666
        assert stats.total_play_time == 600
        assert stats.total_pp == 190.5
        assert stats.unique_players == 2
        assert stats.unique_countries == 2
        assert stats.unique_maps == 2

    def test_recalculate_event_stats_filters_excluded_scores(
        self, stats_event, user, user_stats, beatmap
    ):
        other_user = OsuUser.objects.create(
            id=2,
            username="OtherUser",
            country="us",
            join_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            disabled=False,
        )
        other_user_stats = create_user_stats(other_user.id)

        date = datetime(2024, 6, 10, tzinfo=timezone.utc)
        create_score_with_performance(
            user_stats,
            beatmap,
            Gamemode.STANDARD,
            date,
            count_300=100,
            pp=10.0,
        )
        create_score_with_performance(
            user_stats,
            beatmap,
            Gamemode.STANDARD,
            date,
            count_300=50,
            pp=5.0,
            mutation=ScoreMutation.NO_CHOKE,
        )
        create_score_with_performance(
            user_stats,
            beatmap,
            Gamemode.STANDARD,
            datetime(2023, 1, 1, tzinfo=timezone.utc),
            count_300=40,
            pp=4.0,
        )
        create_score_with_performance(
            other_user_stats,
            beatmap,
            Gamemode.STANDARD,
            date,
            count_300=30,
            pp=3.0,
        )

        stats = recalculate_event_stats(stats_event)

        assert stats.total_scores == 1
        assert stats.total_regular_hits == 100
        assert stats.total_pp == 10.0
        assert stats.unique_players == 1
        assert stats.unique_countries == 1
        assert stats.unique_maps == 1

    def test_recalculate_event_stats_regular_hits_per_gamemode(
        self, stats_event, user, beatmap
    ):
        catch_user_stats = create_user_stats(user.osu_user.id, Gamemode.CATCH)
        taiko_user_stats = create_user_stats(user.osu_user.id, Gamemode.TAIKO)
        mania_user_stats = create_user_stats(user.osu_user.id, Gamemode.MANIA)

        date = datetime(2024, 6, 10, tzinfo=timezone.utc)
        create_score_with_performance(
            catch_user_stats,
            beatmap,
            Gamemode.CATCH,
            date,
            count_300=10,
            count_100=5,
            count_50=5,
        )
        create_score_with_performance(
            taiko_user_stats,
            beatmap,
            Gamemode.TAIKO,
            date,
            count_300=10,
            count_100=5,
        )
        create_score_with_performance(
            mania_user_stats,
            beatmap,
            Gamemode.MANIA,
            date,
            count_300=10,
            count_100=5,
            count_50=5,
            count_geki=2,
            count_katu=3,
        )

        stats = recalculate_event_stats(stats_event)

        assert stats.total_regular_hits == 10 + 15 + 25

    def test_recalculate_event_stats_is_idempotent(
        self, stats_event, user_stats, beatmap
    ):
        date = datetime(2024, 6, 10, tzinfo=timezone.utc)
        create_score_with_performance(
            user_stats,
            beatmap,
            Gamemode.STANDARD,
            date,
            count_300=100,
            count_100=20,
            count_50=5,
            pp=50.5,
        )

        first = recalculate_event_stats(stats_event)
        second = recalculate_event_stats(stats_event)

        for field in (
            "total_scores",
            "total_regular_hits",
            "total_play_time",
            "total_pp",
            "unique_players",
            "unique_countries",
            "unique_maps",
        ):
            assert getattr(first, field) == getattr(second, field)
