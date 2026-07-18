from rest_framework import serializers

from events.models import Event, EventAttendee, EventLeaderboard
from leaderboards.serialisers import LeaderboardSerialiser
from profiles.serialisers import OsuUserSerialiser


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
