from rest_framework import serializers

from events.models import BeatmapChallenge, Event, EventAttendee, EventLeaderboard
from leaderboards.serialisers import LeaderboardSerialiser
from profiles.serialisers import (
    BeatmapSerialiser,
    OsuUserSerialiser,
    ScoreSerialiser,
    UserStatsSerialiser,
)


class EventSerialiser(serializers.ModelSerializer):
    organisers = OsuUserSerialiser(many=True)

    class Meta:
        model = Event
        fields = (
            "id",
            "slug",
            "name",
            "description",
            "logo",
            "theme_colours",
            "start_date",
            "end_date",
            "creation_time",
            "organisers",
        )


class EventAttendeeSerialiser(serializers.ModelSerializer):
    user = OsuUserSerialiser()

    class Meta:
        model = EventAttendee
        fields = (
            "id",
            "user",
        )


class EventLeaderboardSerialiser(serializers.ModelSerializer):
    leaderboard = LeaderboardSerialiser()

    class Meta:
        model = EventLeaderboard
        fields = (
            "id",
            "leaderboard",
        )


class BeatmapChallengeSerialiser(serializers.ModelSerializer):
    beatmap = BeatmapSerialiser(read_only=True)

    class Meta:
        model = BeatmapChallenge
        fields = (
            "id",
            "description",
            "gamemode",
            "challenge_type",
            "beatmap",
        )


class BeatmapChallengeScoreSerialiser(ScoreSerialiser):
    user_stats = UserStatsSerialiser()
