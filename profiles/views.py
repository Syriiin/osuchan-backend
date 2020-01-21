from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.db.models.aggregates import Count

from rest_framework import permissions
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.views import APIView
from rest_framework.response import Response

from common.osu.enums import BeatmapStatus
from osuauth.permissions import BetaPermission
from profiles.enums import ScoreSet
from profiles.models import UserStats, Beatmap, Score
from profiles.serialisers import UserStatsSerialiser, BeatmapSerialiser, UserScoreSerialiser
from profiles.services import fetch_user, fetch_scores
from leaderboards.models import Membership, Invite
from leaderboards.serialisers import UserMembershipSerialiser, UserInviteSerialiser

class GetUserStats(APIView):
    """
    API endpoint for getting UserStats
    """
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, BetaPermission)

    # @method_decorator(cache_page(60 * 2))
    def get(self, request, user_string, gamemode):
        """
        Return UserStats based on a user_string and gamemode
        """
        user_id_type = request.query_params.get("user_id_type") or "id"

        try:
            if user_id_type == "id":
                user_stats = fetch_user(user_id=user_string, gamemode=gamemode)
            elif user_id_type == "username":
                user_stats = fetch_user(username=user_string, gamemode=gamemode)
            else:
                raise NotFound("User not found.")
        except UserStats.DoesNotExist:
            raise NotFound("User not found.")

        serialiser = UserStatsSerialiser(user_stats)
        return Response(serialiser.data)

class GetBeatmaps(APIView):
    """
    API endpoint for getting Beatmaps
    """
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, BetaPermission)

    # @method_decorator(cache_page(60 * 5))
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

    # @method_decorator(cache_page(60 * 2))
    def get(self, request, user_id, gamemode):
        """
        Return Scores based on a user_id and gamemode
        """
        allow_loved = request.query_params.get("allow_loved") == "true" or False
        try:
            score_set = ScoreSet(int(request.query_params.get("score_set")))
        except (ValueError, TypeError):
            score_set = ScoreSet.NORMAL

        scores = Score.objects.select_related("beatmap").non_restricted().filter(user_stats__user_id=user_id, user_stats__gamemode=gamemode)
        if allow_loved:
            scores = scores.filter(beatmap__status__in=[BeatmapStatus.RANKED, BeatmapStatus.APPROVED, BeatmapStatus.LOVED])
        else:
            scores = scores.filter(beatmap__status__in=[BeatmapStatus.RANKED, BeatmapStatus.APPROVED])
        scores = scores.get_score_set(score_set)
        
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
