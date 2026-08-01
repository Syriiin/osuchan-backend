from datetime import datetime, timedelta, timezone

import pytest
from django.core.cache import cache

from common.osu.difficultycalculator import get_default_difficulty_calculator_class
from common.osu.enums import BitMods, Gamemode
from events.models import Event
from profiles.models import (
    DifficultyCalculation,
    OsuUser,
    PerformanceCalculation,
    Score,
    UserStats,
)
from profiles.services import (
    OSU_SCORES_CURSOR_CACHE_KEY,
    calculate_difficulty_values,
    calculate_performance_values,
    fetch_scores,
    fetch_user,
    ingest_scores_from_stream,
    refresh_user_from_api,
    update_difficulty_calculations,
    update_performance_calculations,
)


@pytest.mark.django_db
class TestUserServices:
    def test_fetch_user_not_exists(self):
        assert fetch_user(user_id=1) == None

    def test_fetch_user_by_id(self, user_stats):
        assert fetch_user(user_id=1) == user_stats

    def test_fetch_user_by_username(self, user_stats):
        assert fetch_user(username="TestOsuUser") == user_stats

    def test_refresh_user_not_exists(self):
        assert refresh_user_from_api(user_id=123123) == (None, False)

    def test_refresh_user_from_api(self):
        user_stats, _ = refresh_user_from_api(user_id=5701575)
        assert user_stats is not None
        assert user_stats.user.username == "Syrin"
        assert (
            PerformanceCalculation.objects.filter(
                score__user_stats_id=user_stats.id
            ).count()
            == 14  # 7 scores (6 real, 1 nochoke mutation) * 2 calculators
        )
        assert user_stats.score_style_accuracy == 97.62487865392988
        assert user_stats.score_style_bpm == 201.55895502285534
        assert user_stats.score_style_cs == 4.2766715338147065
        assert user_stats.score_style_ar == 9.742799544873309
        assert user_stats.score_style_od == 8.914664666393149
        assert user_stats.score_style_length == 154.71707503281988

    def test_fetch_scores(self):
        user_stats, _ = refresh_user_from_api(user_id=5701575)
        scores = fetch_scores(user_stats.user_id, [362949], Gamemode.STANDARD)
        assert len(scores) == 12  # 11 real scores + 1 nochoke mutation
        assert user_stats is not None
        user_stats.refresh_from_db()
        assert (
            PerformanceCalculation.objects.filter(
                score__user_stats_id=user_stats.id
            ).count()
            == 38  # 18 scores (17 real, 2 nochoke mutation) * 2 calculators
        )
        assert user_stats.score_style_accuracy == 97.62009555255409
        assert user_stats.score_style_bpm == 203.4815641496913
        assert user_stats.score_style_cs == 4.224451249870312
        assert user_stats.score_style_ar == 9.734107937624676
        assert user_stats.score_style_od == 8.940208492500652
        assert user_stats.score_style_length == 140.06347334630993


@pytest.mark.django_db
class TestDifficultyCalculationServices:
    def test_update_difficulty_calculations(self, beatmap):
        calculation = DifficultyCalculation.objects.create(
            beatmap=beatmap,
            mods=BitMods.NONE,
            calculator_engine="osu.Game.Rulesets.Osu",
            calculator_version="2007.906.0",
        )

        calculation.difficulty_values.create(name="aim", value=0.05)
        calculation.difficulty_values.create(name="dummy", value=9001)

        with get_default_difficulty_calculator_class(
            Gamemode.STANDARD
        )() as difficulty_calculator:
            update_difficulty_calculations([beatmap], difficulty_calculator)

        calculation = DifficultyCalculation.objects.get(
            beatmap_id=beatmap.id, mods=BitMods.NONE
        )

        difficulty_values = calculation.difficulty_values.all()
        assert len(difficulty_values) == 5
        assert difficulty_values[0].name == "aim"
        assert difficulty_values[0].value == 3.809399008867019
        assert difficulty_values[1].name == "speed"
        assert difficulty_values[1].value == 1.564710574509105
        assert difficulty_values[2].name == "flashlight"
        assert difficulty_values[2].value == 0
        assert difficulty_values[3].name == "reading"
        assert difficulty_values[3].value == 1.7803497292117219
        assert difficulty_values[4].name == "total"
        assert difficulty_values[4].value == 6.524323005451468

    def test_update_performance_calculations(self, score):
        difficulty_calculation = DifficultyCalculation.objects.create(
            beatmap=score.beatmap,
            mods=score.mods,
            calculator_engine="osu.Game.Rulesets.Osu",
            calculator_version="2007.906.0",
        )

        difficulty_calculation.difficulty_values.create(name="aim", value=0.05)
        difficulty_calculation.difficulty_values.create(name="dummy", value=9001)

        calculation = PerformanceCalculation.objects.create(
            score=score,
            difficulty_calculation=difficulty_calculation,
            calculator_engine="osu.Game.Rulesets.Osu",
            calculator_version="2007.906.0",
        )

        calculation.performance_values.create(name="aim", value=5.05)
        calculation.performance_values.create(name="dummy", value=900001)

        with get_default_difficulty_calculator_class(
            Gamemode.STANDARD
        )() as difficulty_calculator:
            update_performance_calculations([score], difficulty_calculator)

        difficulty_calculation = DifficultyCalculation.objects.get(
            beatmap_id=score.beatmap_id, mods=score.mods
        )

        difficulty_values = difficulty_calculation.difficulty_values.all()
        assert len(difficulty_values) == 5
        assert difficulty_values[0].name == "aim"
        assert difficulty_values[0].value == 5.593003356550778
        assert difficulty_values[1].name == "speed"
        assert difficulty_values[1].value == 2.1913401312274825
        assert difficulty_values[2].name == "flashlight"
        assert difficulty_values[2].value == 0
        assert difficulty_values[3].name == "reading"
        assert difficulty_values[3].value == 2.4916040541849767
        assert difficulty_values[4].name == "total"
        assert difficulty_values[4].value == 9.528765958388444

        performance_calculation = difficulty_calculation.performance_calculations.get(
            score_id=score.id
        )

        performance_values = performance_calculation.performance_values.all()
        assert len(performance_values) == 6
        assert performance_values[0].name == "aim"
        assert performance_values[0].value == 628.8440218726522
        assert performance_values[1].name == "speed"
        assert performance_values[1].value == 27.079187016931964
        assert performance_values[2].name == "accuracy"
        assert performance_values[2].value == 2.9281890082046083
        assert performance_values[3].name == "flashlight"
        assert performance_values[3].value == 0
        assert performance_values[4].name == "reading"
        assert performance_values[4].value == 48.926436544789105
        assert performance_values[5].name == "total"
        assert performance_values[5].value == 764.5177081010385

    @pytest.fixture
    def difficulty_calculation(self, beatmap):
        return DifficultyCalculation.objects.create(
            beatmap=beatmap,
            mods=BitMods.DOUBLETIME + BitMods.HIDDEN,
            calculator_engine="testcalc",
            calculator_version="v1",
        )

    def test_calculate_difficulty_values(self, difficulty_calculation):
        with get_default_difficulty_calculator_class(
            Gamemode.STANDARD
        )() as difficulty_calculator:
            difficulty_values = calculate_difficulty_values(
                [difficulty_calculation], difficulty_calculator
            )
        assert len(difficulty_values) == 1
        assert len(difficulty_values[0]) == 5
        assert difficulty_values[0][0].name == "aim"
        assert difficulty_values[0][0].value == 5.593003356550778
        assert difficulty_values[0][1].name == "speed"
        assert difficulty_values[0][1].value == 2.1913401312274825
        assert difficulty_values[0][2].name == "flashlight"
        assert difficulty_values[0][2].value == 0
        assert difficulty_values[0][3].name == "reading"
        assert difficulty_values[0][3].value == 2.4916040541849767
        assert difficulty_values[0][4].name == "total"
        assert difficulty_values[0][4].value == 9.528765958388444

    @pytest.fixture
    def performance_calculation(self, score, difficulty_calculation):
        return PerformanceCalculation.objects.create(
            score=score,
            difficulty_calculation=difficulty_calculation,
            calculator_engine="testcalc",
            calculator_version="v1",
        )

    def test_calculate_performance_values(self, performance_calculation):
        with get_default_difficulty_calculator_class(
            Gamemode.STANDARD
        )() as difficulty_calculator:
            performance_values = calculate_performance_values(
                [performance_calculation], difficulty_calculator
            )
        assert len(performance_values) == 1
        assert len(performance_values[0]) == 6
        assert performance_values[0][0].name == "aim"
        assert performance_values[0][0].value == 628.8440218726522
        assert performance_values[0][1].name == "speed"
        assert performance_values[0][1].value == 27.079187016931964
        assert performance_values[0][2].name == "accuracy"
        assert performance_values[0][2].value == 2.9281890082046083
        assert performance_values[0][3].name == "flashlight"
        assert performance_values[0][3].value == 0
        assert performance_values[0][4].name == "reading"
        assert performance_values[0][4].value == 48.926436544789105
        assert performance_values[0][5].name == "total"
        assert performance_values[0][5].value == 764.5177081010385


@pytest.mark.django_db
class TestIngestScoresFromStream:
    def test_stream_populates_db_and_updates_user_stats(self):
        cache.delete(OSU_SCORES_CURSOR_CACHE_KEY)

        osu_user = OsuUser.objects.create(
            id=5701575,
            username="Syrin",
            country="au",
            join_date=datetime(2017, 1, 1, tzinfo=timezone.utc),
            disabled=False,
        )
        user_stats = UserStats.objects.create(
            user=osu_user,
            gamemode=Gamemode.STANDARD,
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
            last_updated=datetime.now(tz=timezone.utc),
        )

        now = datetime.now(tz=timezone.utc)
        event = Event.objects.create(
            slug="test-event",
            name="Test Event",
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(days=1),
            creation_time=now,
        )
        event.attendees.add(osu_user)

        ingest_scores_from_stream()

        user_stats.refresh_from_db()
        assert Score.objects.filter(user_stats=user_stats).count() > 0
        assert PerformanceCalculation.objects.filter(
            score__user_stats=user_stats
        ).exists()
        assert user_stats.score_style_accuracy != 0
        assert user_stats.score_style_bpm != 0

        cache.delete(OSU_SCORES_CURSOR_CACHE_KEY)
