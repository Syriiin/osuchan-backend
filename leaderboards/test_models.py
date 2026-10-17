from types import SimpleNamespace

import pytest

from leaderboards.models import Invite, Leaderboard, Membership


@pytest.mark.django_db
class TestLeaderboard:
    def test_magic_str(self, leaderboard: Leaderboard):
        assert str(leaderboard) == "test leaderboard"

    def test_get_merged_top_scores_merges_and_keeps_ordering(self):
        leaderboard = Leaderboard(
            top_scores=[
                {"score_id": 1, "value": 100.0, "user_id": 1},
                {"score_id": 2, "value": 90.0, "user_id": 2},
            ]
        )
        member_scores = [
            SimpleNamespace(id=3, performance_total=110.0),
            SimpleNamespace(id=4, performance_total=95.0),
        ]
        assert leaderboard.get_merged_top_scores(1, member_scores) == [
            {"score_id": 3, "value": 110.0, "user_id": 1},
            {"score_id": 4, "value": 95.0, "user_id": 1},
            {"score_id": 2, "value": 90.0, "user_id": 2},
        ]

    def test_get_merged_top_scores_removes_member_when_no_scores(self):
        leaderboard = Leaderboard(
            top_scores=[
                {"score_id": 1, "value": 100.0, "user_id": 1},
                {"score_id": 2, "value": 90.0, "user_id": 2},
            ]
        )
        assert leaderboard.get_merged_top_scores(1, []) == [
            {"score_id": 2, "value": 90.0, "user_id": 2}
        ]

    def test_get_merged_top_scores_caps_at_100(self):
        leaderboard = Leaderboard(
            top_scores=[
                {"score_id": i, "value": float(i), "user_id": 2} for i in range(100)
            ]
        )
        member_scores = [SimpleNamespace(id=1000, performance_total=1000.0)]
        merged = leaderboard.get_merged_top_scores(1, member_scores)
        assert len(merged) == 100
        assert merged[0] == {"score_id": 1000, "value": 1000.0, "user_id": 1}
        assert max(score["value"] for score in merged[1:]) == 99.0

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
        assert str(membership) == "test leaderboard: TestOsuUser"

    def test_recalculate(self):
        # TODO: this
        pass


@pytest.mark.django_db
class TestInvite:
    def test_magic_str(self, invite: Invite):
        assert str(invite) == "test leaderboard: TestOsuUser"
