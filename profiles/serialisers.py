from rest_framework import serializers
from osuauth.models import User

from profiles.models import Beatmap, OsuUser, Score, ScoreFilter, UserStats


class UserSerialiser(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("is_staff", "is_beta_tester", "last_active")


class OsuUserSerialiser(serializers.ModelSerializer):
    user = UserSerialiser()

    class Meta:
        model = OsuUser
        fields = (
            # osu data
            "id",
            "username",
            "country",
            "join_date",
            # relations
            "user",
        )


class UserStatsSerialiser(serializers.ModelSerializer):
    user = OsuUserSerialiser()

    class Meta:
        model = UserStats
        fields = (
            "id",
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
            "score_style_accuracy",
            "score_style_bpm",
            "score_style_cs",
            "score_style_ar",
            "score_style_od",
            "score_style_length",
            # relations
            "user",
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
            "submission_date",
            "approval_date",
            "last_updated",
            # difficulty
            "difficulty_total",
            # relations
            "creator",
        )


class ScoreSerialiser(serializers.ModelSerializer):
    class Meta:
        model = Score
        fields = (
            "id",
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
            "date",
            # osuchan data
            "result",
            # difficulty
            "performance_total",
            "nochoke_performance_total",
            "difficulty_total",
            # relations
            "beatmap",
            "user_stats",
            # convenience fields
            "gamemode",
            "accuracy",
            "bpm",
            "length",
            "circle_size",
            "approach_rate",
            "overall_difficulty",
        )


class UserScoreSerialiser(ScoreSerialiser):
    beatmap = BeatmapSerialiser()


class BeatmapScoreSerialiser(ScoreSerialiser):
    user_stats = UserStatsSerialiser()


class ScoreFilterSerialiser(serializers.ModelSerializer):
    class Meta:
        model = ScoreFilter
        fields = (
            "id",
            # score criteria
            "allowed_beatmap_status",
            "oldest_beatmap_date",
            "newest_beatmap_date",
            "oldest_score_date",
            "newest_score_date",
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
            "lowest_length",
            "highest_length",
        )
