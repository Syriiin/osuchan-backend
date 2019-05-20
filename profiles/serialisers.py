from django.contrib.auth.models import Group

from rest_framework import serializers

from profiles.models import OsuUser, UserStats, Beatmap, Score

class OsuUserSerialiser(serializers.ModelSerializer):
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
            "rank",
            "country_rank",
            "pp",
            "accuracy",
            # osuchan data
            "nochoke_pp",
            "score_style_accuracy",
            "score_style_bpm",
            "score_style_cs",
            "score_style_ar",
            "score_style_od",
            "score_style_length",
            # relations
            "user"
        )

class BeatmapSerialiser(serializers.ModelSerializer):
    class Meta:
        model = Beatmap
        fields = (
            # osu data
            "id",
            "set_id",
            "artist",
            "title",
            "difficulty_name",
            "gamemode",
            "status",
            "creator_name",
            "bpm",
            "drain_time",
            "total_time",
            "max_combo",
            "circle_size",
            "overall_difficulty",
            "approach_rate",
            "health_drain",
            "star_rating",
            "last_updated",
            # relations ids
            "creator_id"
        )

class ScoreSerialiser(serializers.ModelSerializer):
    beatmap = BeatmapSerialiser()
    
    class Meta:
        model = Score
        fields = (
            # osu data
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
            # osuchan data
            "nochoke_pp",
            "star_rating",
            "result",
            # relations
            "beatmap",
            # convenience fields
            "accuracy",
            "bpm",
            "length",
            "circle_size",
            "approach_rate",
            "overall_difficulty"
        )
