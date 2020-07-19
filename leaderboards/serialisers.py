from rest_framework import serializers

from profiles.serialisers import OsuUserSerialiser, ScoreSerialiser, UserStatsSerialiser, BeatmapSerialiser, ScoreFilterSerialiser
from leaderboards.models import Leaderboard, Membership, Invite

class LeaderboardSerialiser(serializers.ModelSerializer):
    score_filter = ScoreFilterSerialiser()
    owner = OsuUserSerialiser()

    class Meta:
        model = Leaderboard
        fields = (
            "id",
            "gamemode",
            "score_set",
            "access_type",
            "name",
            "description",
            "icon_url",
            "allow_past_scores",
            "member_count",
            "archived",
            # relations
            "score_filter",
            "owner",
            # dates
            "creation_time"
        )

class MembershipSerialiser(serializers.ModelSerializer):
    class Meta:
        model = Membership
        fields = (
            "id",
            "pp",
            "score_count",
            "rank",
            # relations
            "leaderboard",
            "user",
            # dates
            "join_date"
        )

class LeaderboardMembershipSerialiser(MembershipSerialiser):
    user = OsuUserSerialiser()

class UserMembershipSerialiser(MembershipSerialiser):
    leaderboard = LeaderboardSerialiser()

class InviteSerialiser(serializers.ModelSerializer):
    class Meta:
        model = Invite
        fields = (
            "id",
            "message",
            # relations
            "leaderboard",
            "user",
            # dates
            "invite_date"
        )

class LeaderboardInviteSerialiser(InviteSerialiser):
    user = OsuUserSerialiser()

class UserInviteSerialiser(InviteSerialiser):
    leaderboard = LeaderboardSerialiser()

class LeaderboardScoreSerialiser(ScoreSerialiser):
    user_stats = UserStatsSerialiser()
    beatmap = BeatmapSerialiser()
