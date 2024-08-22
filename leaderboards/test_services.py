import pytest

from common.osu.enums import Gamemode
from leaderboards.enums import LeaderboardAccessType
from leaderboards.models import Leaderboard
from leaderboards.services import (
    create_leaderboard,
    create_membership,
    update_membership,
)
from profiles.enums import ScoreSet
from profiles.models import ScoreFilter
from profiles.services import fetch_scores


@pytest.mark.django_db
class TestMembershipServices:

    def test_nochoke_leaderboard(self, stub_user_stats, score_filter):
        leaderboard = create_leaderboard(
            stub_user_stats.user_id,
            Leaderboard(
                gamemode=Gamemode.STANDARD,
                score_set=ScoreSet.NEVER_CHOKE,
                access_type=LeaderboardAccessType.PUBLIC,
                name="test nochoke leaderboard",
                description="test nochoke leaderboard",
                icon_url="",
                allow_past_scores=True,
                member_count=0,
                archived=False,
                notification_discord_webhook_url="",
                score_filter=ScoreFilter.objects.create(),
            ),
        )
        membership = leaderboard.memberships.first()
        assert membership.score_count == 4
        assert membership.pp == 1239.449243038565

    @pytest.fixture
    def membership(self, leaderboard, stub_user_stats):
        return create_membership(leaderboard.id, stub_user_stats.user_id)

    def test_create_membership(self, leaderboard, membership):
        assert membership.leaderboard == leaderboard
        assert membership.leaderboard.member_count == 2
        assert membership.user.username == "Syrin"
        assert membership.score_count == 4
        assert membership.pp == 1215.5272384251844

    def test_update_membership(self, membership):
        fetch_scores(membership.user_id, [362949], Gamemode.STANDARD)
        membership = update_membership(membership.leaderboard, membership.user_id)
        assert membership.score_count == 5
        assert membership.pp == 1399.2214430030024
