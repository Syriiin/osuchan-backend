from django.utils.decorators import method_decorator
from django.db.models.aggregates import Count

from rest_framework import permissions
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.views import APIView
from rest_framework.response import Response

from common.utils import parse_int_or_none, parse_float_or_none
from common.osu.enums import BeatmapStatus, Mods, Gamemode
from osuauth.permissions import BetaPermission
from profiles.enums import ScoreSet, AllowedBeatmapStatus
from profiles.models import UserStats, Beatmap, Score, ScoreFilter
from profiles.serialisers import UserStatsSerialiser, BeatmapSerialiser, UserScoreSerialiser
from profiles.services import fetch_user, fetch_scores
from leaderboards.models import Membership, Invite
from leaderboards.serialisers import UserMembershipSerialiser, UserInviteSerialiser

class GetUserStats(APIView):
    """
    API endpoint for getting UserStats
    """
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, BetaPermission)

    def get(self, request, user_string, gamemode):
        """
        Return UserStats based on a user_string and gamemode
        """
        user_id_type = request.query_params.get("user_id_type", "id")

        try:
            if user_id_type == "id":
                user_stats = fetch_user(user_id=user_string, gamemode=gamemode)
            elif user_id_type == "username":
                user_stats = fetch_user(username=user_string, gamemode=gamemode)
            else:
                raise NotFound("User not found.")

            # Show not found for disabled (restricted) users
            if user_stats.user.disabled:
                raise NotFound("User not found.")
        except UserStats.DoesNotExist:
            raise NotFound("User not found.")

        serialiser = UserStatsSerialiser(user_stats)
        return Response(serialiser.data)

class GetBeatmap(APIView):
    """
    API endpoint for getting Beatmaps
    """
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, BetaPermission)

    def get(self, request, beatmap_id):
        """
        Return Beatmap based on a beatmap_id
        """

        try:
            beatmap = Beatmap.objects.get(id=beatmap_id)
        except Beatmap.DoesNotExist:
            raise NotFound("Beatmap not found.")

        serialiser = BeatmapSerialiser(beatmap)
        return Response(serialiser.data)

class ListUserScores(APIView):
    """
    API endpoint for Scores
    """
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, BetaPermission)

    def get(self, request, user_id, gamemode):
        """
        Return Scores based on a user_id, gamemode, score_set, and various filters
        """
        score_filter = ScoreFilter(
            allowed_beatmap_status=parse_int_or_none(request.query_params.get("allowed_beatmap_status", AllowedBeatmapStatus.RANKED_ONLY)),
            oldest_beatmap_date=request.query_params.get("oldest_beatmap_date"),
            newest_beatmap_date=request.query_params.get("newest_beatmap_date"),
            oldest_score_date=request.query_params.get("oldest_score_date"),
            newest_score_date=request.query_params.get("newest_score_date"),
            lowest_ar=parse_float_or_none(request.query_params.get("lowest_ar")),
            highest_ar=parse_float_or_none(request.query_params.get("highest_ar")),
            lowest_od=parse_float_or_none(request.query_params.get("lowest_od")),
            highest_od=parse_float_or_none(request.query_params.get("highest_od")),
            lowest_cs=parse_float_or_none(request.query_params.get("lowest_cs")),
            highest_cs=parse_float_or_none(request.query_params.get("highest_cs")),
            required_mods=parse_int_or_none(request.query_params.get("required_mods", Mods.NONE)),
            disqualified_mods=parse_int_or_none(request.query_params.get("disqualified_mods", Mods.NONE)),
            lowest_accuracy=parse_float_or_none(request.query_params.get("lowest_accuracy")),
            highest_accuracy=parse_float_or_none(request.query_params.get("highest_accuracy")),
            lowest_length=parse_float_or_none(request.query_params.get("lowest_length")),
            highest_length=parse_float_or_none(request.query_params.get("highest_length"))
        )
        score_set = parse_int_or_none(request.query_params.get("score_set", ScoreSet.NORMAL))
        if gamemode != Gamemode.STANDARD:
            # score set is not supported yet by non-standard gamemodes since they dont support chokes
            score_set = ScoreSet.NORMAL

        scores = Score.objects.select_related("beatmap").non_restricted().filter(user_stats__user_id=user_id, user_stats__gamemode=gamemode).apply_score_filter(score_filter).get_score_set(score_set)
        
        serialiser = UserScoreSerialiser(scores[:100], many=True)
        return Response(serialiser.data)
    
    def post(self, request, user_id, gamemode):
        """
        Add new Scores based on passes user_id, gamemode, beatmap_ids
        """
        scores = fetch_scores(user_id, request.data.get("beatmap_ids"), gamemode)
        serialiser = UserScoreSerialiser(scores, many=True)
        return Response(serialiser.data)

class ListUserMemberships(APIView):
    """
    API endpoint for listing Memberships for an OsuUser
    """
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, BetaPermission)

    def get(self, request, user_id):
        if not request.user.is_authenticated or request.user.osu_user_id != user_id:
            raise PermissionDenied("You may only retrieve memberships for the authenticated user.")
        memberships = Membership.objects.select_related("leaderboard", "leaderboard__owner").annotate(score_count=Count("scores")).filter(user_id=user_id)
        serialiser = UserMembershipSerialiser(memberships, many=True)
        return Response(serialiser.data)

class ListUserInvites(APIView):
    """
    API endpoint for listing Invites for an OsuUser
    """
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, BetaPermission)

    def get(self, request, user_id):
        if not request.user.is_authenticated or request.user.osu_user_id != user_id:
            raise PermissionDenied("You may only retrieve invites for the authenticated user.")
        invites = Invite.objects.select_related("leaderboard", "leaderboard__owner").filter(user_id=user_id)
        serialiser = UserInviteSerialiser(invites, many=True)
        return Response(serialiser.data)
