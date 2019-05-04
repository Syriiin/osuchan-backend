from django.contrib.auth.models import Group

from rest_framework import viewsets, permissions, mixins
from rest_framework.response import Response

from profiles.models import UserStats, Score
from profiles.serialisers import UserStatsSerialiser, ScoreSerialiser

class UserStatsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows userstats to be viewed.
    """
    queryset = UserStats.objects.non_restricted()
    serializer_class = UserStatsSerialiser

class ScoreViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    """
    API endpoint that allows scores to be viewed.
    """
    queryset = Score.objects.non_restricted()
    serializer_class = ScoreSerialiser
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def create(self, request):
        data = request.data
        scores = Score.objects.create_or_update(data["beatmap_id"], data["user_id"], data["gamemode"])
        serialiser = ScoreSerialiser(scores, many=True)
        return Response(serialiser.data)
