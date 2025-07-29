from django.conf import settings
from rest_framework import permissions
from rest_framework.exceptions import NotFound, ParseError, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from common.osu.enums import Gamemode
from ppraces.enums import PPRaceStatus
from ppraces.models import PPRace, PPRacePlayer, PPRaceTeam
from ppraces.serialisers import (
    PPRacePlayerSerialiser,
    PPRaceSerialiser,
    PPRacesScoreSerialiser,
)
from ppraces.services import create_pprace_lobby, start_pprace
from ppraces.tasks import update_pprace_players
from profiles.tasks import update_user_recent


class PPRaceList(APIView):
    """
    API endpoint for listing pp races
    """

    authentication_classes = []
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        """
        Create a new pp race
        """

        api_key = request.query_params.get("api_key")
        if api_key != settings.COE_API_KEY:
            raise PermissionDenied("Invalid API key.")

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


class PPRaceStart(APIView):
    """
    API endpoint to start a pp race
    """

    authentication_classes = []
    permission_classes = (permissions.AllowAny,)

    def post(self, request, pprace_id):
        api_key = request.query_params.get("api_key")
        if api_key != settings.COE_API_KEY:
            raise PermissionDenied("Invalid API key.")

        try:
            pprace = PPRace.objects.get(id=pprace_id)
        except PPRace.DoesNotExist:
            raise NotFound("PP race not found.")

        if pprace.status != PPRaceStatus.LOBBY:
            raise ParseError("PP race is not in lobby state.")

        pprace = start_pprace(pprace)
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


class PPRacePlayerTriggerUpdate(APIView):
    """
    API endpoint to force an update for a user
    """

    authentication_classes = []
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        api_key = request.query_params.get("api_key")
        if api_key != settings.COE_API_KEY:
            raise PermissionDenied("Invalid API key.")

        user_id = request.query_params.get("user_id")
        if user_id is None:
            raise ParseError("Missing user_id parameter.")
        try:
            user_id = int(user_id)
        except ValueError:
            raise ParseError("Invalid user_id parameter.")

        gamemode = request.query_params.get("gamemode")
        if gamemode is None:
            raise ParseError("Missing gamemode parameter.")
        try:
            gamemode = Gamemode(int(gamemode))
        except ValueError:
            raise ParseError("Invalid gamemode parameter.")

        update_user_recent(user_id, gamemode, cooldown_seconds=0)
        update_pprace_players(user_id=user_id, gamemode=gamemode)

        return Response({"status": "success"})
