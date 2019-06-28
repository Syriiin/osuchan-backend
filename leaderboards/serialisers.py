from rest_framework import serializers

from profiles.serialisers import OsuUserSerialiser
from leaderboards.models import Leaderboard, Membership

class LeaderboardSerialiser(serializers.ModelSerializer):
    owner = OsuUserSerialiser()
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Leaderboard
        fields = (
            "id",
            "gamemode",
            "visibility",
            "name",
            # score criteria
            "allowed_beatmap_status",
            "oldest_beatmap_date",
            "newest_beatmap_date",
            "lowest_ar",
            "highest_ar",
            "lowest_od",
            "highest_od",
            "lowest_cs",
            "highest_cs",
            "required_mods",
            "disqualified_mods",
            "lowest_accuracy",
            "highest_accuracy",
            # relations
            "owner",
            # dates
            "creation_time",
            # methods
            "member_count"
        )
        
    def get_member_count(self, obj):
        return obj.members.count()

class MembershipSerialiser(serializers.ModelSerializer):
    user = OsuUserSerialiser()

    class Meta:
        model = Membership
        fields = (
            "pp",
            # relations
            "leaderboard",
            "user",
            # dates
            "join_date"
        )
