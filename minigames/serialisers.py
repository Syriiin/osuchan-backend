from rest_framework import serializers

from minigames.models import Minigame, MinigamePlayer, MinigameScore, MinigameTeam
from profiles.serialisers import (
    BeatmapSerialiser,
    OsuUserSerialiser,
    ScoreSerialiser,
    UserStatsSerialiser,
)


class MinigamePlayerSerialiser(serializers.ModelSerializer):
    user = OsuUserSerialiser()

    class Meta:
        model = MinigamePlayer
        fields = ("id", "points", "score_count", "user")


class MinigameTeamSerialiser(serializers.ModelSerializer):
    players = MinigamePlayerSerialiser(many=True)

    class Meta:
        model = MinigameTeam
        fields = ("id", "name", "points", "score_count", "players")


class MinigameSerialiser(serializers.ModelSerializer):
    teams = MinigameTeamSerialiser(many=True)
    host = OsuUserSerialiser()

    class Meta:
        model = Minigame
        fields = (
            "id",
            "game_type",
            "name",
            "gamemode",
            "status",
            "start_time",
            "end_time",
            "config",
            "state",
            "created_at",
            "host",
            "is_free_for_all",
            "teams",
            "winning_team",
        )


class MinigameScoreSerialiser(ScoreSerialiser):
    user_stats = UserStatsSerialiser()
    beatmap = BeatmapSerialiser()


class MinigameScoringScoreSerialiser(serializers.ModelSerializer):
    score = MinigameScoreSerialiser()

    class Meta:
        model = MinigameScore
        fields = ("id", "points", "score")
