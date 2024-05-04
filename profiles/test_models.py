import pytest

from common.osu.difficultycalculator import DifficultyCalculator
from common.osu.enums import Mods
from profiles.enums import ScoreResult
from profiles.models import (
    Beatmap,
    DifficultyCalculation,
    OsuUser,
    PerformanceCalculation,
    Score,
    UserStats,
)


@pytest.mark.django_db
class TestOsuUser:
    def test_magic_str(self, osu_user: OsuUser):
        assert str(osu_user) == "TestOsuUser"


@pytest.mark.django_db
class TestUserStats:
    def test_magic_str(self, user_stats: UserStats):
        assert str(user_stats) == "STANDARD: 1"

    def test_add_scores_from_data(self):
        # TODO: test this (without mocking?) or move to service
        pass

    def test_recalculate(self):
        # TODO: this
        pass


@pytest.mark.django_db
class TestBeatmap:
    def test_magic_str(self, beatmap: Beatmap):
        assert (
            str(beatmap)
            == "test artist - test title [test difficulty] (by test creator)"
        )

    def test_from_data(self):
        # TODO: this
        pass

    def test_update_difficulty_values(self, beatmap: Beatmap):
        beatmap.update_difficulty_values(DifficultyCalculator)
        assert beatmap.difficulty_total == 6.711556915919059
        assert beatmap.difficulty_calculator_engine == "rosu-pp-py"
        assert beatmap.difficulty_calculator_version == "1.0.0"


@pytest.mark.django_db
class TestScore:
    def test_magic_str(self, score: Score):
        assert str(score) == "1: 395pp"

    def test_process(self, score: Score):
        score.process()
        assert score.result == ScoreResult.END_CHOKE
        assert score.performance_total == 395.282
        assert score.nochoke_performance_total == 626.7353926695473
        assert score.difficulty_total == 8.975730066553297
        assert score.difficulty_calculator_engine == "legacy"
        assert score.difficulty_calculator_version == "legacy"

    def test_update_performance_values(self, score: Score):
        score.update_performance_values(DifficultyCalculator)
        assert score.performance_total == 626.7353926695473
        assert score.nochoke_performance_total == 626.7353926695473
        assert score.difficulty_total == 8.975730066553297
        assert score.difficulty_calculator_engine == "rosu-pp-py"
        assert score.difficulty_calculator_version == "1.0.0"


@pytest.fixture
def difficulty_calculation(beatmap: Beatmap):
    return DifficultyCalculation.objects.create(
        beatmap=beatmap,
        mods=Mods.DOUBLETIME + Mods.HIDDEN,
        calculator_engine="testcalc",
        calculator_version="v1",
    )


@pytest.mark.django_db
class TestDifficultyCalculation:
    def test_calculate_difficulty_values(
        self, difficulty_calculation: DifficultyCalculation
    ):
        difficulty_values = difficulty_calculation.calculate_difficulty_values(
            DifficultyCalculator
        )
        assert len(difficulty_values) == 1
        assert difficulty_values[0].name == "total"
        assert difficulty_values[0].value == 8.975730066553297


@pytest.mark.django_db
class TestPerformanceCalculation:
    @pytest.fixture
    def performance_calculation(
        self, score: Score, difficulty_calculation: DifficultyCalculation
    ):
        return PerformanceCalculation.objects.create(
            score=score,
            difficulty_calculation=difficulty_calculation,
            calculator_engine="testcalc",
            calculator_version="v1",
        )

    def test_calculate_performance_values(
        self, performance_calculation: PerformanceCalculation
    ):
        performance_values = performance_calculation.calculate_performance_values(
            performance_calculation.score, DifficultyCalculator
        )
        assert len(performance_values) == 1
        assert performance_values[0].name == "total"
        assert performance_values[0].value == 626.7353926695473
