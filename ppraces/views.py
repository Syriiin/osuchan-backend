from rest_framework import permissions
from rest_framework.exceptions import NotFound, ParseError, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from common.osu.enums import Gamemode
from ppraces.models import PPRace, PPRaceTeam
from ppraces.serialisers import PPRaceSerialiser, PPRacesScoreSerialiser
from ppraces.services import create_pprace_lobby


class PPRaceList(APIView):
    """
    API endpoint for listing pp races
    """

    def post(self, request):
        """
        Create a new pp race
        """
        # check user is staff
        if not request.user.is_staff:
            raise PermissionDenied("You do not have permission to create a pp race.")

        name = request.data.get("name")
        if name is None:
            raise ParseError("Missing name parameter.")
        gamemode = request.data.get("gamemode")
        if gamemode is None:
            raise ParseError("Missing gamemode parameter.")
        try:
            gamemode = Gamemode(gamemode)
        except ValueError:
            raise ParseError("Invalid gamemode parameter.")

        teams = request.data.get("teams")
        if not isinstance(teams, dict):
            raise ParseError("Invalid teams parameter.")

        pprace = create_pprace_lobby(
            name=name,
            gamemode=gamemode,
            teams=teams,
        )
        serialiser = PPRaceSerialiser(pprace)
        return Response(serialiser.data)


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
