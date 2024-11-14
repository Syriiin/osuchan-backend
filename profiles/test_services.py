import pytest

from common.osu.difficultycalculator import get_default_difficulty_calculator_class
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
        assert refresh_user_from_api(user_id=123123) == (None, False)

    def test_refresh_user_from_api(self):
        user_stats, _ = refresh_user_from_api(user_id=5701575)
        assert user_stats is not None
        assert user_stats.user.username == "Syrin"
        assert (
            PerformanceCalculation.objects.filter(
                score__user_stats_id=user_stats.id
            ).count()
            == 12  # 6 scores (5 real, 1 nochoke mutation) * 2 calculators
        )
        assert user_stats.score_style_accuracy == 98.23948233070676
        assert user_stats.score_style_bpm == 211.857710839314
        assert user_stats.score_style_cs == 4.3374150072441795
        assert user_stats.score_style_ar == 9.914417601671216
        assert user_stats.score_style_od == 9.115480081314509
        assert user_stats.score_style_length == 163.6261778811056

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
            == 36  # 18 scores (16 real, 2 nochoke mutation) * 2 calculators
        )
        assert user_stats.score_style_accuracy == 98.09793775692621
        assert user_stats.score_style_bpm == 211.85490142989167
        assert user_stats.score_style_cs == 4.262837957123972
        assert user_stats.score_style_ar == 9.866657641491493
        assert user_stats.score_style_od == 9.101007366108535
        assert user_stats.score_style_length == 144.47806905456227


@pytest.mark.django_db
class TestDifficultyCalculationServices:
    def test_update_difficulty_calculations(self, beatmap):
        calculation = DifficultyCalculation.objects.create(
            beatmap=beatmap,
            mods=Mods.NONE,
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
            beatmap_id=beatmap.id, mods=Mods.NONE
        )

        difficulty_values = calculation.difficulty_values.all()
        assert len(difficulty_values) == 4
        assert difficulty_values[0].name == "aim"
        assert difficulty_values[0].value == 3.757355457446509
        assert difficulty_values[1].name == "speed"
        assert difficulty_values[1].value == 2.235918611275225
        assert difficulty_values[2].name == "flashlight"
        assert difficulty_values[2].value == 0
        assert difficulty_values[3].name == "total"
        assert difficulty_values[3].value == 6.717114400082113

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
        assert len(difficulty_values) == 4
        assert difficulty_values[0].name == "aim"
        assert difficulty_values[0].value == 5.02576598317138
        assert difficulty_values[1].name == "speed"
        assert difficulty_values[1].value == 2.991169729323895
        assert difficulty_values[2].name == "flashlight"
        assert difficulty_values[2].value == 0
        assert difficulty_values[3].name == "total"
        assert difficulty_values[3].value == 8.98257099312042

        performance_calculation = difficulty_calculation.performance_calculations.get(
            score_id=score.id
        )

        performance_values = performance_calculation.performance_values.all()
        assert len(performance_values) == 5
        assert performance_values[0].name == "aim"
        assert performance_values[0].value == 495.13336284361014
        assert performance_values[1].name == "speed"
        assert performance_values[1].value == 70.12310156350622
        assert performance_values[2].name == "accuracy"
        assert performance_values[2].value == 3.199536008089327
        assert performance_values[3].name == "flashlight"
        assert performance_values[3].value == 0
        assert performance_values[4].name == "total"
        assert performance_values[4].value == 631.3916342933587

    @pytest.fixture
    def difficulty_calculation(self, beatmap):
        return DifficultyCalculation.objects.create(
            beatmap=beatmap,
            mods=Mods.DOUBLETIME + Mods.HIDDEN,
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
        assert len(difficulty_values[0]) == 4
        assert difficulty_values[0][0].name == "aim"
        assert difficulty_values[0][0].value == 5.02576598317138
        assert difficulty_values[0][1].name == "speed"
        assert difficulty_values[0][1].value == 2.991169729323895
        assert difficulty_values[0][2].name == "flashlight"
        assert difficulty_values[0][2].value == 0
        assert difficulty_values[0][3].name == "total"
        assert difficulty_values[0][3].value == 8.98257099312042

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
        assert len(performance_values[0]) == 5
        assert performance_values[0][0].name == "aim"
        assert performance_values[0][0].value == 495.13336284361014
        assert performance_values[0][1].name == "speed"
        assert performance_values[0][1].value == 70.12310156350622
        assert performance_values[0][2].name == "accuracy"
        assert performance_values[0][2].value == 3.199536008089327
        assert performance_values[0][3].name == "flashlight"
        assert performance_values[0][3].value == 0
        assert performance_values[0][4].name == "total"
        assert performance_values[0][4].value == 631.3916342933587
