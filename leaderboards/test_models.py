import pytest

from common.osu.enums import Gamemode
from leaderboards.enums import LeaderboardAccessType
from leaderboards.models import Invite, Leaderboard, Membership
from profiles.enums import ScoreSet
from profiles.models import OsuUser, ScoreFilter


@pytest.fixture
def leaderboard(score_filter: ScoreFilter):
    return Leaderboard.objects.create(
        gamemode=Gamemode.STANDARD,
        score_set=ScoreSet.NORMAL,
        access_type=LeaderboardAccessType.GLOBAL,
        name="TestLeaderboard",
        description="Test leaderboard",
        icon_url="",
        allow_past_scores=True,
        member_count=0,
        notification_discord_webhook_url="",
        score_filter=score_filter,
    )


@pytest.mark.django_db
class TestLeaderboard:
    def test_magic_str(self, leaderboard: Leaderboard):
        assert str(leaderboard) == "[STANDARD] TestLeaderboard"

    def test_get_pp_record(self):
        # TODO: this
        pass

    def test_get_top_membership(self):
        # TODO: this
        pass

    def test_update_membership(self):
        # TODO: this
        pass

    def test_update_member_count(self):
        # TODO: this
        pass


@pytest.mark.django_db
class TestMembership:
    @pytest.fixture
    def membership(self, leaderboard: Leaderboard, osu_user: OsuUser):
        return Membership.objects.create(
            pp=0, score_count=0, rank=1, leaderboard=leaderboard, user=osu_user
        )

    def test_magic_str(self, membership: Membership):
        assert str(membership) == "[STANDARD] TestLeaderboard: TestOsuUser"

    def test_recalculate(self):
        # TODO: this
        pass


@pytest.mark.django_db
class TestInvite:
    @pytest.fixture
    def invite(self, leaderboard: Leaderboard, osu_user: OsuUser):
        return Invite.objects.create(
            message="test invite message", leaderboard=leaderboard, user=osu_user
        )

    def test_magic_str(self, invite: Invite):
        assert str(invite) == "[STANDARD] TestLeaderboard: TestOsuUser"
