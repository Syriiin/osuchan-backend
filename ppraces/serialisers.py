from rest_framework import serializers

from ppraces.models import PPRace, PPRacePlayer, PPRaceTeam
from profiles.serialisers import (
    BeatmapSerialiser,
    OsuUserSerialiser,
    ScoreSerialiser,
    UserStatsSerialiser,
)


class PPRacesScoreSerialiser(ScoreSerialiser):
    user_stats = UserStatsSerialiser()
    beatmap = BeatmapSerialiser()


class PPRacePlayerSerialiser(serializers.ModelSerializer):
    user = OsuUserSerialiser()

    class Meta:
        model = PPRacePlayer
        fields = (
            "id",
            "pp",
            "pp_contribution",
            "score_count",
            # relations
            "user",
        )


class PPRaceTeamSerialiser(serializers.ModelSerializer):
    players = PPRacePlayerSerialiser(many=True)

    class Meta:
        model = PPRaceTeam
        fields = (
            "id",
            "name",
            "total_pp",
            "score_count",
            # relations
            "players",
        )


class PPRaceSerialiser(serializers.ModelSerializer):
    teams = PPRaceTeamSerialiser(many=True)

    class Meta:
        model = PPRace
        fields = (
            "id",
            "name",
            "gamemode",
            "status",
            "start_time",
            "end_time",
            "pp_decay_base",
            # relations
            "teams",
        )
