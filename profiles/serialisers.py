from django.contrib.auth.models import Group

from rest_framework import serializers

from profiles.models import OsuUser, UserStats, Beatmap, Score

class OsuUserSerialiser(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = OsuUser
        fields = ("url", "username")

class UserStatsSerialiser(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = UserStats
        fields = ("url", "gamemode")

class BeatmapSerialiser(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Beatmap
        fields = ("url", "title")

class ScoreSerialiser(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Score
        fields = ("url", "pp")
