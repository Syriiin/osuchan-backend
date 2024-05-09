import pytest

from common.osu.difficultycalculator import DifficultyCalculator
from common.osu.enums import Mods
from profiles.models import DifficultyCalculation, PerformanceCalculation
from profiles.services import (
    calculate_difficulty_values,
    calculate_performance_values,
    fetch_user,
    refresh_user_from_api,
    update_difficulty_calculations,
    update_performance_calculation,
    update_performance_calculations_for_unique_beatmap,
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
        assert user_stats.user.username == "Syrin"
        assert (
            PerformanceCalculation.objects.filter(
                score__user_stats_id=user_stats.id
            ).count()
            == 5
        )


@pytest.mark.django_db
class TestDifficultyCalculationServices:
    def test_update_difficulty_calculations(self, beatmap):
        difficulty_calculator = DifficultyCalculator()
        update_difficulty_calculations([beatmap], difficulty_calculator)

        calculation = DifficultyCalculation.objects.get(
            beatmap_id=beatmap.id, mods=Mods.NONE
        )

        difficulty_values = calculation.difficulty_values.all()
        assert len(difficulty_values) == 1
        assert difficulty_values[0].name == "total"
        assert difficulty_values[0].value == 6.711556915919059

    def test_update_performance_calculations_for_unique_beatmap(self, score):
        difficulty_calculator = DifficultyCalculator()
        update_performance_calculations_for_unique_beatmap(
            score.beatmap_id, score.mods, [score], difficulty_calculator
        )

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

    def test_update_performance_calculation(
        self,
        score,
    ):
        difficulty_calculator = DifficultyCalculator()
        update_performance_calculation(score, difficulty_calculator)

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
        difficulty_values = calculate_difficulty_values(
            [difficulty_calculation], DifficultyCalculator()
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
        performance_values = calculate_performance_values(
            [performance_calculation], DifficultyCalculator()
        )
        assert len(performance_values) == 1
        assert len(performance_values[0]) == 1
        assert performance_values[0][0].name == "total"
        assert performance_values[0][0].value == 626.7353926695473
