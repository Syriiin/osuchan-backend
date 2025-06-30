from rest_framework import serializers

from ppraces.models import PPRace, PPRacePlayer, PPRaceScore, PPRaceTeam
from profiles.serialisers import BeatmapSerialiser, OsuUserSerialiser, ScoreSerialiser


class PPRacesScoreSerialiser(ScoreSerialiser):
    beatmap = BeatmapSerialiser()


class PPRacePlayerSerialiser(serializers.ModelSerializer):
    scores = PPRacesScoreSerialiser(many=True)
    user = OsuUserSerialiser()

    class Meta:
        model = PPRacePlayer
        fields = (
            "id",
            "pp",
            "score_count",
            # relations
            "user",
            "scores",
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
            "duration",
            "start_time",
            "end_time",
            # relations
            "teams",
        )
