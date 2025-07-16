from rest_framework import permissions
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from ppraces.models import PPRace, PPRaceTeam
from ppraces.serialisers import PPRaceSerialiser, PPRacesScoreSerialiser


class PPRaceDetail(APIView):
    """
    API endpoint for specific pp races
    """

    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get(self, request, pprace_id):
        try:
            pprace = PPRace.objects.prefetch_related("teams__players__user").get(
                id=pprace_id
            )
        except PPRace.DoesNotExist:
            raise NotFound("PP race not found.")

        serialiser = PPRaceSerialiser(pprace)
        return Response(serialiser.data)


class PPRaceRecentScoresList(APIView):
    """
    API endpoint for recent scores
    """

    def get(self, request, pprace_id):
        try:
            pprace = PPRace.objects.get(id=pprace_id)
        except PPRace.DoesNotExist:
            raise NotFound("PP race not found.")

        scores = (
            pprace.get_recent_scores()
            .select_related("user_stats", "user_stats__user", "beatmap")
            .prefetch_related(
                "performance_calculations__performance_values",
                "performance_calculations__difficulty_calculation__difficulty_values",
            )
        )

        serialiser = PPRacesScoreSerialiser(scores, many=True)
        return Response(serialiser.data)


class PPRaceTeamScoresList(APIView):
    """
    API endpoint for team top scores
    """

    def get(self, request, pprace_id, team_id):
        try:
            pprace = PPRace.objects.get(id=pprace_id)
        except PPRace.DoesNotExist:
            raise NotFound("PP race not found.")

        try:
            team = pprace.teams.get(id=team_id)
        except PPRaceTeam.DoesNotExist:
            raise NotFound("Team not found.")

        scores = (
            team.get_top_scores()
            .select_related("user_stats", "user_stats__user", "beatmap")
            .prefetch_related(
                "performance_calculations__performance_values",
                "performance_calculations__difficulty_calculation__difficulty_values",
            )
        )

        serialiser = PPRacesScoreSerialiser(scores, many=True)
        return Response(serialiser.data)
