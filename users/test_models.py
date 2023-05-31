import pytest

from osuauth.models import User
from profiles.models import ScoreFilter
from users.models import ScoreFilterPreset


@pytest.mark.django_db
class TestScoreFilterPreset:
    @pytest.fixture
    def score_filter_preset(self, user: User, score_filter: ScoreFilter):
        return ScoreFilterPreset.objects.create(
            name="Hidden", user=user, score_filter=score_filter
        )

    def test_magic_str(self, score_filter_preset):
        assert str(score_filter_preset) == f"{score_filter_preset.user_id}: Hidden"
