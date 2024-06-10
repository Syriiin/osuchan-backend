import pytest

from common.osu.difficultycalculator import get_difficulty_calculator_class
from profiles.enums import ScoreResult
from profiles.models import Beatmap, OsuUser, Score, UserStats


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
        beatmap.update_difficulty_values(get_difficulty_calculator_class("rosupp"))
        assert beatmap.difficulty_total == 6.711556915919059
        assert beatmap.difficulty_calculator_engine == "rosu-pp-py"
        assert beatmap.difficulty_calculator_version == "1.0.1"


@pytest.mark.django_db
class TestScore:
    def test_process(self, score: Score):
        score.process()
        assert score.result == ScoreResult.END_CHOKE
        assert score.nochoke_performance_total == 626.7353926695473

    def test_update_performance_values(self, score: Score):
        score.update_performance_values(get_difficulty_calculator_class("rosupp"))
        assert score.performance_total == 626.7353926695473
        assert score.nochoke_performance_total == 626.7353926695473
        assert score.difficulty_total == 8.975730066553297
        assert score.difficulty_calculator_engine == "rosu-pp-py"
        assert score.difficulty_calculator_version == "1.0.1"
