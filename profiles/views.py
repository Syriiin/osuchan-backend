from django.contrib.auth.models import Group

from rest_framework import routers, viewsets

from profiles.models import OsuUser, UserStats, Beatmap, Score
from profiles.serialisers import OsuUserSerialiser, UserStatsSerialiser, BeatmapSerialiser, ScoreSerialiser

class OsuUserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows osuusers to be viewed or edited.
    """
    queryset = OsuUser.objects.all()
    serializer_class = OsuUserSerialiser

class UserStatsViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows userstats to be viewed or edited.
    """
    queryset = UserStats.objects.all()
    serializer_class = UserStatsSerialiser

class BeatmapViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows beatmaps to be viewed or edited.
    """
    queryset = Beatmap.objects.all()
    serializer_class = BeatmapSerialiser

class ScoreViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows scores to be viewed or edited.
    """
    queryset = Score.objects.all()
    serializer_class = ScoreSerialiser
