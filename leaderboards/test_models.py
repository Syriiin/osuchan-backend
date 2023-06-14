import pytest

from leaderboards.models import Invite, Leaderboard, Membership
from profiles.models import OsuUser


@pytest.mark.django_db
class TestLeaderboard:
    def test_magic_str(self, leaderboard: Leaderboard):
        assert str(leaderboard) == "[STANDARD] test leaderboard"

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
    def test_magic_str(self, membership: Membership):
        assert str(membership) == "[STANDARD] test leaderboard: TestOsuUser"

    def test_recalculate(self):
        # TODO: this
        pass


@pytest.mark.django_db
class TestInvite:
    def test_magic_str(self, invite: Invite):
        assert str(invite) == "[STANDARD] test leaderboard: TestOsuUser"
