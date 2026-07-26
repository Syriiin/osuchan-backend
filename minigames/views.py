from django.conf import settings
from rest_framework import permissions
from rest_framework.exceptions import NotFound, ParseError, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from common.osu.enums import Gamemode
from minigames.enums import MinigameStatus
from minigames.games import game_registry
from minigames.models import Minigame, MinigamePlayer, MinigameScore, MinigameTeam
from minigames.serialisers import (
    MinigamePlayerSerialiser,
    MinigameScoreSerialiser,
    MinigameScoringScoreSerialiser,
    MinigameSerialiser,
)
from minigames.services import (
    create_minigame,
    delete_minigame,
    join_minigame,
    leave_minigame,
    move_minigame_team,
    start_minigame,
    update_minigame_settings,
)
from profiles.models import Score


class MinigameList(APIView):
    """List all minigames, or create a new one."""

    def get(self, request):
        statuses = request.query_params.get("statuses")
        if statuses:
            status_list = [s.strip() for s in statuses.split(",") if s.strip()]
            games = Minigame.objects.filter(status__in=status_list)
        else:
            games = Minigame.objects.filter(status__in=["lobby", "waiting_to_start"])
        games = games.prefetch_related("teams__players__user")
        serialiser = MinigameSerialiser(games, many=True)
        return Response(serialiser.data)

    def post(self, request):
        if not request.user.is_authenticated:
            raise PermissionDenied("Authentication required.")

        if request.user.osu_user is None:
            raise PermissionDenied("No osu! account linked.")

        game_type = request.data.get("game_type")
        if game_type is None:
            raise ParseError("Missing game_type parameter.")

        if game_type not in game_registry:
            raise NotFound("Unknown game type.")

        if request.user.osu_user_id not in settings.MINIGAMES_BETA_WHITELIST:
            raise PermissionDenied("Minigames are in closed beta.")

        name = request.data.get("name")
        if name is None:
            raise ParseError("Missing name parameter.")

        gamemode = request.data.get("gamemode")
        if gamemode is None:
            raise ParseError("Missing gamemode parameter.")
        try:
            gamemode_enum = Gamemode(int(gamemode))
        except ValueError, TypeError:
            raise ParseError("Invalid gamemode parameter.")

        if gamemode_enum != Gamemode.STANDARD:
            raise ParseError("Only standard gamemode is supported for minigames.")

        is_free_for_all = request.data.get("is_free_for_all", False)

        if not isinstance(is_free_for_all, bool):
            raise ParseError("Invalid is_free_for_all parameter.")

        if is_free_for_all:
            teams = None
        else:
            teams = request.data.get("teams")
            if not isinstance(teams, list):
                raise ParseError("Invalid teams parameter.")
            if len(teams) < 2:
                raise ParseError("Must have at least 2 teams.")

        game_settings = request.data.get("settings", {})

        minigame = create_minigame(
            game_type=game_type,
            name=name,
            gamemode=gamemode_enum,
            host=request.user.osu_user,
            settings_data=game_settings,
            teams=teams,
            is_free_for_all=is_free_for_all,
        )
        serialiser = MinigameSerialiser(minigame)
        return Response(serialiser.data)


class MinigameHistoryList(APIView):
    """List minigames the current user has joined."""

    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        if request.user.osu_user is None:
            raise PermissionDenied("No osu! account linked.")

        minigames = (
            Minigame.objects.filter(teams__players__user=request.user.osu_user)
            .distinct()
            .prefetch_related("teams__players__user")
            .order_by("-created_at")
        )
        serialiser = MinigameSerialiser(minigames, many=True)
        return Response(serialiser.data)


class MinigameDetail(APIView):
    """Get details for a specific minigame."""

    def get(self, request, game_id):
        try:
            minigame = Minigame.objects.prefetch_related("teams__players__user").get(
                id=game_id
            )
        except Minigame.DoesNotExist:
            raise NotFound("Game not found.")

        serialiser = MinigameSerialiser(minigame)
        return Response(serialiser.data)

    def delete(self, request, game_id):
        try:
            minigame = Minigame.objects.get(id=game_id)
        except Minigame.DoesNotExist:
            raise NotFound("Game not found.")

        if minigame.status != MinigameStatus.LOBBY:
            raise ParseError("Game is not in lobby state.")

        if request.user.osu_user != minigame.host:
            raise PermissionDenied("Only the host can delete the game.")

        delete_minigame(minigame)
        return Response(status=204)


class MinigameStart(APIView):
    """Start a minigame lobby with a countdown."""

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, game_id):
        try:
            minigame = Minigame.objects.get(id=game_id)
        except Minigame.DoesNotExist:
            raise NotFound("Game not found.")

        if minigame.status != MinigameStatus.LOBBY:
            raise ParseError("Game is not in lobby state.")

        if request.user.osu_user != minigame.host:
            raise PermissionDenied("Only the host can start the game.")

        non_empty_teams = [t for t in minigame.teams.all() if t.players.exists()]
        if len(non_empty_teams) < 2:
            raise ParseError("Need at least 2 non-empty teams to start.")

        countdown = request.data.get("countdown", 60)

        try:
            countdown = int(countdown)
        except ValueError, TypeError:
            raise ParseError("Invalid countdown parameter.")

        if countdown < 10 or countdown > 60:
            raise ParseError("countdown must be between 10 and 60 seconds")

        minigame = start_minigame(minigame, countdown)
        serialiser = MinigameSerialiser(minigame)
        return Response(serialiser.data)


class MinigameRecentScoresList(APIView):
    """List recent scores in a minigame."""

    def get(self, request, game_id):
        try:
            minigame = Minigame.objects.get(id=game_id)
        except Minigame.DoesNotExist:
            raise NotFound("Game not found.")

        try:
            limit = min(
                int(request.query_params.get("limit", 10)),
                50,
            )
        except ValueError, TypeError:
            limit = 10

        scores = (
            Score.objects.filter(minigame_scores__minigame=minigame)
            .select_related("user_stats", "user_stats__user", "beatmap")
            .prefetch_related(
                "performance_calculations__performance_values",
                "performance_calculations__difficulty_calculation__difficulty_values",
            )
            .order_by("-date")[:limit]
        )

        serialiser = MinigameScoreSerialiser(scores, many=True)
        return Response(serialiser.data)


class MinigameScoringScoresList(APIView):
    """List all scores with non-zero points in a minigame."""

    def get(self, request, game_id):
        try:
            minigame = Minigame.objects.get(id=game_id)
        except Minigame.DoesNotExist:
            raise NotFound("Game not found.")

        minigame_scores = (
            MinigameScore.objects.filter(minigame=minigame, points__gt=0)
            .select_related(
                "score__user_stats",
                "score__user_stats__user",
                "score__beatmap",
            )
            .prefetch_related(
                "score__performance_calculations__performance_values",
                "score__performance_calculations__difficulty_calculation__difficulty_values",
            )
            .order_by("score__date")
        )

        serialiser = MinigameScoringScoreSerialiser(minigame_scores, many=True)
        return Response(serialiser.data)


class MinigameJoin(APIView):
    """Join a minigame lobby."""

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, game_id):
        if request.user.osu_user is None:
            raise PermissionDenied("No osu! account linked.")

        if request.user.osu_user_id not in settings.MINIGAMES_BETA_WHITELIST:
            raise PermissionDenied("Minigames are in closed beta.")

        try:
            minigame = Minigame.objects.get(id=game_id)
        except Minigame.DoesNotExist:
            raise NotFound("Game not found.")

        if minigame.status not in (
            MinigameStatus.LOBBY,
            MinigameStatus.WAITING_TO_START,
        ):
            raise ParseError("Game has started.")

        if MinigamePlayer.objects.filter(
            user=request.user.osu_user,
            team__minigame__status__in=(
                MinigameStatus.LOBBY,
                MinigameStatus.WAITING_TO_START,
                MinigameStatus.IN_PROGRESS,
                MinigameStatus.FINALISING,
            ),
        ).exists():
            raise ParseError("Player is already in an active minigame.")

        player = join_minigame(minigame, request.user.osu_user)

        serialiser = MinigamePlayerSerialiser(player)
        return Response(serialiser.data)


class MinigameLeave(APIView):
    """Leave a minigame lobby."""

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, game_id):
        if request.user.osu_user is None:
            raise PermissionDenied("No osu! account linked.")

        try:
            minigame = Minigame.objects.get(id=game_id)
        except Minigame.DoesNotExist:
            raise NotFound("Game not found.")

        if minigame.status not in (
            MinigameStatus.LOBBY,
            MinigameStatus.WAITING_TO_START,
        ):
            raise ParseError("Cannot leave game at this stage.")

        if not MinigamePlayer.objects.filter(
            team__minigame=minigame, user=request.user.osu_user
        ).exists():
            raise ParseError("Player is not in this game.")

        leave_minigame(minigame, request.user.osu_user)

        return Response({"detail": "Left the game."})


class MinigameUpdateSettings(APIView):
    """Update a minigame lobby's settings."""

    permission_classes = (permissions.IsAuthenticated,)

    def patch(self, request, game_id):
        if request.user.osu_user is None:
            raise PermissionDenied("No osu! account linked.")

        try:
            minigame = Minigame.objects.get(id=game_id)
        except Minigame.DoesNotExist:
            raise NotFound("Game not found.")

        if minigame.status != MinigameStatus.LOBBY:
            raise ParseError("Can only change settings while in lobby.")

        if request.user.osu_user != minigame.host:
            raise PermissionDenied("Only the host can change settings.")

        game_settings = request.data.get("settings", {})

        minigame = update_minigame_settings(minigame, game_settings)

        serialiser = MinigameSerialiser(minigame)
        return Response(serialiser.data)


class MinigameMoveTeam(APIView):
    """Move a player to another team."""

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, game_id):
        if request.user.osu_user is None:
            raise PermissionDenied("No osu! account linked.")

        team_id = request.data.get("team_id")
        if team_id is None:
            raise ParseError("Missing team_id parameter.")

        try:
            minigame = Minigame.objects.get(id=game_id)
        except Minigame.DoesNotExist:
            raise NotFound("Game not found.")

        if minigame.is_free_for_all:
            raise ParseError("Cannot move teams in free-for-all.")

        if minigame.status not in (
            MinigameStatus.LOBBY,
            MinigameStatus.WAITING_TO_START,
        ):
            raise ParseError("Game has started.")

        if not minigame.teams.filter(id=team_id).exists():
            raise ParseError("Team does not belong to this game.")

        if not MinigamePlayer.objects.filter(
            team__minigame=minigame, user=request.user.osu_user
        ).exists():
            raise ParseError("Player is not in this game.")

        player = move_minigame_team(minigame, request.user.osu_user, team_id)

        serialiser = MinigamePlayerSerialiser(player)
        return Response(serialiser.data)
