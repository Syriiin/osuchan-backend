import pytest

from common.osu.enums import Gamemode
from leaderboards.services import create_membership, update_membership
from profiles.services import fetch_scores


@pytest.mark.django_db
class TestMembershipServices:
    @pytest.fixture
    def membership(self, leaderboard, stub_user_stats):
        return create_membership(leaderboard.id, stub_user_stats.user_id)

    def test_create_membership(self, leaderboard, membership):
        assert membership.leaderboard == leaderboard
        assert membership.leaderboard.member_count == 2
        assert membership.user.username == "Syrin"
        assert membership.score_count == 4
        assert membership.pp == 1215.8880634205632

    def test_update_membership(self, membership):
        fetch_scores(membership.user_id, [362949], Gamemode.STANDARD)
        membership = update_membership(membership.leaderboard, membership.user_id)
        assert membership.score_count == 5
        assert membership.pp == 1399.645425686207
