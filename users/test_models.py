import pytest

from users.models import ScoreFilterPreset


class TestScoreFilterPreset:
    @pytest.fixture
    def score_filter_preset(self):
        return ScoreFilterPreset(id=1, name="HD only", user_id=2)

    def test_magic_str(self, score_filter_preset):
        assert str(score_filter_preset) == "2: HD only"
