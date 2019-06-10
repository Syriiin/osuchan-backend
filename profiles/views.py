from django.contrib.auth.models import Group
from django.http import Http404

from rest_framework import viewsets, permissions, mixins
from rest_framework.views import APIView
from rest_framework.response import Response

from profiles.models import UserStats, Score
from profiles.serialisers import UserStatsSerialiser, ScoreSerialiser

class GetUserStats(APIView):
    """
    API endpoint for getting UserStats
    """
    queryset = UserStats.objects.non_restricted()

    def get(self, request, user_string, gamemode):
        """
        Return UserStats based on a user_string and gamemode
        """
        # TODO: support either user_id or username as search value (frontend should send username if search or non-number url, else id)
        # temp fix for updating users until rewrite of managers
        try:
            # temp only allow username
            user_stats = UserStats.objects.create_or_update(username=user_string, gamemode=gamemode)
        except UserStats.DoesNotExist:
            raise Http404

        # try:
        #     user_stats = self.queryset.get(gamemode=gamemode, user_id=int(user_string))
        # except (UserStats.DoesNotExist, ValueError):
        #     try:
        #         user_stats = self.queryset.get(gamemode=gamemode, user__username__iexact=user_string)
        #     except UserStats.DoesNotExist:
        #         raise Http404

        serialiser = UserStatsSerialiser(user_stats)
        return Response(serialiser.data)

class GetUserScores(APIView):
    """
    API endpoint for getting Scores
    """
    queryset = UserStats.objects.non_restricted()

    def get(self, request, user_string, gamemode):
        """
        Return UserStats based on a user_string and gamemode
        """
        try:
            user_stats = self.queryset.get(gamemode=gamemode, user_id=int(user_string))
        except (UserStats.DoesNotExist, ValueError):
            try:
                user_stats = self.queryset.get(gamemode=gamemode, user__username__iexact=user_string)
            except UserStats.DoesNotExist:
                raise Http404
            
        scores = user_stats.scores.unique_maps()[:100]

        serialiser = ScoreSerialiser(scores, many=True)
        return Response(serialiser.data)

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
