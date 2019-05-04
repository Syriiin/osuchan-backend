from django.contrib.auth.models import Group

from rest_framework import serializers

from profiles.models import OsuUser, UserStats, Score

class OsuUserSerialiser(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = OsuUser
        fields = (
            # osu data
            "id",
            "username",
            "country",
            "join_date"
        )

class UserStatsSerialiser(serializers.ModelSerializer):
    user = OsuUserSerialiser()

    class Meta:
        model = UserStats
        fields = (
            # osu data
            "gamemode",
            "playcount",
            "playtime",
            "level",
            "ranked_score",
            "total_score",
            "rank",
            "country_rank",
            "pp",
            "accuracy",
            "count_300",
            "count_100",
            "count_50",
            "count_rank_ss",
            "count_rank_ssh",
            "count_rank_s",
            "count_rank_sh",
            "count_rank_a",
            # osuchan data
            "extra_pp",
            "nochoke_pp",
            # relations
            "user"
        )

class ScoreSerialiser(serializers.ModelSerializer):
    class Meta:
        model = Score
        fields = (
            "score",
            "count_300",
            "count_100",
            "count_50",
            "count_miss",
            "count_geki",
            "count_katu",
            "best_combo",
            "perfect",
            "mods",
            "rank",
            "pp",
            "date",
            "nochoke_pp",
            "result"
        )
