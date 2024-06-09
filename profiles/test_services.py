import pytest

from common.osu.difficultycalculator import get_difficulty_calculator_class
from common.osu.enums import Gamemode, Mods
from profiles.models import DifficultyCalculation, PerformanceCalculation
from profiles.services import (
    calculate_difficulty_values,
    calculate_performance_values,
    fetch_scores,
    fetch_user,
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
        assert refresh_user_from_api(user_id=123123) == None

    def test_refresh_user_from_api(self):
        user_stats = refresh_user_from_api(user_id=5701575)
        assert user_stats is not None
        assert user_stats.user.username == "Syrin"
        assert (
            PerformanceCalculation.objects.filter(
                score__user_stats_id=user_stats.id
            ).count()
            == 15  # 5 scores * 3 calculators
        )
        assert user_stats.score_style_accuracy == 97.30060082707615
        assert user_stats.score_style_bpm == 204.68228666627067
        assert user_stats.score_style_cs == 4.402689732435789
        assert user_stats.score_style_ar == 9.839811659329108
        assert user_stats.score_style_od == 9.004677665408208
        assert user_stats.score_style_length == 158.83277363433214

    def test_fetch_scores(self):
        user_stats = refresh_user_from_api(user_id=5701575)
        scores = fetch_scores(user_stats.user_id, [362949], Gamemode.STANDARD)
        assert len(scores) == 12  # 11 real scores + 1 nochoke mutation
        assert user_stats is not None
        user_stats.refresh_from_db()
        assert (
            PerformanceCalculation.objects.filter(
                score__user_stats_id=user_stats.id
            ).count()
            == 54  # 18 scores (16 real, 2 nochoke mutation) * 3 calculators
        )
        assert user_stats.score_style_accuracy == 97.3569373221504
        assert user_stats.score_style_bpm == 206.03421080151674
        assert user_stats.score_style_cs == 4.326684182174256
        assert user_stats.score_style_ar == 9.813108376003889
        assert user_stats.score_style_od == 9.013232015574896
        assert user_stats.score_style_length == 143.385919158249


@pytest.mark.django_db
class TestDifficultyCalculationServices:
    def test_update_difficulty_calculations(self, beatmap):
        with get_difficulty_calculator_class("rosupp")() as difficulty_calculator:
            update_difficulty_calculations([beatmap], difficulty_calculator)

        calculation = DifficultyCalculation.objects.get(
            beatmap_id=beatmap.id, mods=Mods.NONE
        )

        difficulty_values = calculation.difficulty_values.all()
        assert len(difficulty_values) == 1
        assert difficulty_values[0].name == "total"
        assert difficulty_values[0].value == 6.711556915919059

    def test_update_performance_calculations(self, score):
        with get_difficulty_calculator_class("rosupp")() as difficulty_calculator:
            update_performance_calculations([score], difficulty_calculator)

        difficulty_calculation = DifficultyCalculation.objects.get(
            beatmap_id=score.beatmap_id, mods=score.mods
        )

        difficulty_values = difficulty_calculation.difficulty_values.all()
        assert len(difficulty_values) == 1
        assert difficulty_values[0].name == "total"
        assert difficulty_values[0].value == 8.975730066553297

        performance_calculation = difficulty_calculation.performance_calculations.get(
            score_id=score.id
        )

        performance_values = performance_calculation.performance_values.all()
        assert len(performance_values) == 1
        assert performance_values[0].name == "total"
        assert performance_values[0].value == 626.7353926695473

    @pytest.fixture
    def difficulty_calculation(self, beatmap):
        return DifficultyCalculation.objects.create(
            beatmap=beatmap,
            mods=Mods.DOUBLETIME + Mods.HIDDEN,
            calculator_engine="testcalc",
            calculator_version="v1",
        )

    def test_calculate_difficulty_values(self, difficulty_calculation):
        with get_difficulty_calculator_class("rosupp")() as difficulty_calculator:
            difficulty_values = calculate_difficulty_values(
                [difficulty_calculation], difficulty_calculator
            )
        assert len(difficulty_values) == 1
        assert len(difficulty_values[0]) == 1
        assert difficulty_values[0][0].name == "total"
        assert difficulty_values[0][0].value == 8.975730066553297

    @pytest.fixture
    def performance_calculation(self, score, difficulty_calculation):
        return PerformanceCalculation.objects.create(
            score=score,
            difficulty_calculation=difficulty_calculation,
            calculator_engine="testcalc",
            calculator_version="v1",
        )

    def test_calculate_performance_values(self, performance_calculation):
        with get_difficulty_calculator_class("rosupp")() as difficulty_calculator:
            performance_values = calculate_performance_values(
                [performance_calculation], difficulty_calculator
            )
        assert len(performance_values) == 1
        assert len(performance_values[0]) == 1
        assert performance_values[0][0].name == "total"
        assert performance_values[0][0].value == 626.7353926695473
