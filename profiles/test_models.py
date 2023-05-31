import pytest

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

    def test_update_difficulty_values(self):
        # TODO: this
        pass


@pytest.mark.django_db
class TestScore:
    def test_magic_str(self, score: Score):
        assert str(score) == "1: 395pp"

    def test_process(self):
        # TODO: this
        pass

    def test_update_performance_values(self):
        # TODO: this
        pass
