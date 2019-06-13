from django.contrib.auth.models import Group
from django.http import Http404

from rest_framework import viewsets, permissions, mixins
from rest_framework.views import APIView
from rest_framework.response import Response

from profiles.models import UserStats, Score
from profiles.serialisers import UserStatsSerialiser, ScoreSerialiser
from profiles.services import fetch_user, fetch_scores

class GetUserStats(APIView):
    """
    API endpoint for getting UserStats
    """
    queryset = UserStats.objects.non_restricted()

    def get(self, request, user_string, gamemode):
        """
        Return UserStats based on a user_string and gamemode
        """
        user_id_type = request.query_params.get("user_id_type")

        try:
            if user_id_type == "id":
                user_stats = fetch_user(user_id=user_string, gamemode=gamemode)
            elif user_id_type == "username":
                user_stats = fetch_user(username=user_string, gamemode=gamemode)
            else:
                raise Http404
        except UserStats.DoesNotExist:
            raise Http404

        serialiser = UserStatsSerialiser(user_stats)
        return Response(serialiser.data)

class ListUserScores(APIView):
    """
    API endpoint for Scores
    """
    queryset = Score.objects.select_related("beatmap").non_restricted()
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get(self, request):
        """
        Return Scores based on a user_id and gamemode
        """
        user_id = request.query_params.get("user_id")
        gamemode = request.query_params.get("gamemode")
        if user_id and gamemode:
            scores = self.queryset.filter(user_stats__user_id=user_id, user_stats__gamemode=gamemode).unique_maps()[:100]
        else:
            scores = self.queryset.unique_maps()[:100]

        serialiser = ScoreSerialiser(scores, many=True)
        return Response(serialiser.data)
    
    def post(self, request):
        """
        Add new Scores based on passes user_id, gamemode, beatmap_id
        """
        data = request.data
        scores = fetch_scores(data["user_id"], data["beatmap_id"], data["gamemode"])
        serialiser = ScoreSerialiser(scores, many=True)
        return Response(serialiser.data)
