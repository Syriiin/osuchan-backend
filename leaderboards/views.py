from rest_framework import permissions
from rest_framework.exceptions import ParseError, PermissionDenied, NotFound
from rest_framework.views import APIView
from rest_framework.response import Response

from common.osu.enums import Mod
from osuauth.permissions import BetaPermission
from profiles.models import Score
from profiles.serialisers import ScoreSerialiser
from leaderboards.models import Leaderboard, Membership, Invite
from leaderboards.serialisers import LeaderboardSerialiser, MembershipSerialiser, InviteSerialiser
from leaderboards.services import create_leaderboard, create_membership
from leaderboards.enums import LeaderboardAccessType, AllowedBeatmapStatus

class ListLeaderboards(APIView):
    """
    API endpoint for listing Leaderboards
    """    
    queryset = Leaderboard.objects.select_related("owner").all()
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, BetaPermission)

    def get(self, request):
        osu_user = None if request.user.is_anonymous else request.user.osu_user
        leaderboards = self.queryset.visible_to(osu_user)
        
        user_id = request.query_params.get("user_id")
        gamemode = request.query_params.get("gamemode")
        if user_id is not None:
            # filtering for leaderboards with a specific member
            leaderboards = leaderboards.filter(members__id=user_id)
        if gamemode is not None:
            # Filtering for leaderboards for a speficic gamemode
            leaderboards = leaderboards.filter(gamemode=gamemode)

        serialiser = LeaderboardSerialiser(leaderboards, many=True)
        return Response(serialiser.data)

    def post(self, request):
        # Check required parameters
        if not request.user.is_authenticated:
            raise PermissionDenied("Must be logged in to perform this action.")
        else:
            user_id = request.user.osu_user_id

        gamemode = request.data.get("gamemode")
        if gamemode is None:
            raise ParseError("Missing gamemode parameter.")
        
        access_type = request.data.get("access_type")
        if access_type is None:
            raise ParseError("Missing access_type parameter.")
        elif access_type == LeaderboardAccessType.GLOBAL:
            raise ParseError("Parameter access_type must be either 1 for public, or 2 for private.")
        
        name = request.data.get("name")
        if name is None:
            raise ParseError("Missing name parameter.")
        
        leaderboard = Leaderboard(
            gamemode=gamemode,
            access_type=access_type,
            name=name
        )

        # Set optional score criteria
        leaderboard.allow_past_scores = request.data.get("allow_past_scores") if request.data.get("allow_past_scores") is not None else True
        leaderboard.allowed_beatmap_status = request.data.get("allowed_beatmap_status") or AllowedBeatmapStatus.RANKED_ONLY
        leaderboard.oldest_beatmap_date = request.data.get("oldest_beatmap_date")
        leaderboard.newest_beatmap_date = request.data.get("newest_beatmap_date")
        leaderboard.lowest_ar = request.data.get("lowest_ar")
        leaderboard.highest_ar = request.data.get("highest_ar")
        leaderboard.lowest_od = request.data.get("lowest_od")
        leaderboard.highest_od = request.data.get("highest_od")
        leaderboard.lowest_cs = request.data.get("lowest_cs")
        leaderboard.highest_cs = request.data.get("highest_cs")
        leaderboard.required_mods = request.data.get("required_mods") or Mod.NONE
        leaderboard.disqualified_mods = request.data.get("disqualified_mods") or Mod.NONE
        leaderboard.lowest_accuracy = request.data.get("lowest_accuracy")
        leaderboard.highest_accuracy = request.data.get("highest_accuracy")
        
        # Hand off to create_leaderboard service to set relations, update owner membership, and save
        leaderboard = create_leaderboard(user_id, leaderboard)

        serialiser = LeaderboardSerialiser(leaderboard)
        return Response(serialiser.data)

class GetLeaderboard(APIView):
    """
    API endpoint for specific Leaderboards
    """
    queryset = Leaderboard.objects.all()
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, BetaPermission)

    def get(self, request, leaderboard_id):
        osu_user = None if request.user.is_anonymous else request.user.osu_user
        try:
            leaderboard = self.queryset.visible_to(osu_user).get(id=leaderboard_id)
        except Leaderboard.DoesNotExist:
            raise NotFound("Leaderboard not found.")
        serialiser = LeaderboardSerialiser(leaderboard)
        return Response(serialiser.data)

    def delete(self, request, leaderboard_id):
        if not request.user.is_authenticated:
            raise PermissionDenied("Must be logged in to perform this action.")
        else:
            user_id = request.user.osu_user_id
        try:
            leaderboard = self.queryset.get(id=leaderboard_id)
        except Leaderboard.DoesNotExist:
            raise NotFound("Leaderboard not found.")
        if leaderboard.owner_id != user_id:
            raise PermissionDenied("Must be the leaderboard owner to perform this action.")
        return Response(leaderboard.delete())

class ListMembers(APIView):
    """
    API endpoint for listing Memberships
    """
    queryset = Membership.objects.select_related("user").order_by("-pp").all()
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, BetaPermission)

    def get(self, request):
        leaderboard_id = request.query_params.get("leaderboard_id")
        
        # If no leaderboard_id was passed, raise 404
        if not leaderboard_id:
            raise ParseError("Missing leaderboard_id query parameter.")

        memberships = self.queryset.filter(leaderboard_id=leaderboard_id)
        serialiser = MembershipSerialiser(memberships, many=True)
        return Response(serialiser.data)

    def post(self, request):
        if not request.user.is_authenticated:
            raise PermissionDenied("Must be logged in to perform this action.")
        else:
            user_id = request.user.osu_user_id

        leaderboard_id = request.data.get("leaderboard_id")

        # If no leaderboard_id was passed, raise 404
        if leaderboard_id is None:
            raise ParseError("Missing leaderboard_id parameter.")

        membership = create_membership(leaderboard_id, user_id)
        serialiser = MembershipSerialiser(membership)
        return Response(serialiser.data)

class GetMember(APIView):
    """
    API endpoint for specific Members
    """
    queryset = Membership.objects.select_related("user").all()
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, BetaPermission)

    def get(self, request, user_id):
        leaderboard_id = request.query_params.get("leaderboard_id")

        # If no leaderboard_id was passed, raise 404
        if not leaderboard_id:
            raise ParseError("Missing leaderboard_id query parameter.")
        
        membership = self.queryset.get(leaderboard_id=leaderboard_id, user_id=user_id)
        serialiser = MembershipSerialiser(membership)
        return Response(serialiser.data)

    def delete(self, request, user_id):
        leaderboard_id = request.query_params.get("leaderboard_id")
        
        # If no leaderboard_id was passed, raise 404
        if not leaderboard_id:
            raise ParseError("Missing leaderboard_id query parameter.")
        
        membership = self.queryset.get(leaderboard_id=leaderboard_id, user_id=user_id)
        return Response(membership.delete())

class ListInvites(APIView):
    """
    API endpoint for listing Invites
    """
    queryset = Invite.objects.all()
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, BetaPermission)

    def get(self, request):
        leaderboard_id = request.query_params.get("leaderboard_id")
        user_id = request.query_params.get("user_id")
        
        # If no leaderboard_id or user_id was passed, raise 404
        if leaderboard_id is not None:
            invites = self.queryset.filter(leaderboard_id=leaderboard_id)
        elif user_id is not None:
            invites = self.queryset.filter(user_id=user_id)
        else:
            raise ParseError("Must pass either user_id or leaderboard_id as a query parameter.")

        serialiser = InviteSerialiser(invites, many=True)
        return Response(serialiser.data)

    def post(self, request):
        if not request.user.is_authenticated:
            raise PermissionDenied("Must be logged in to perform this action.")
        else:
            user_id = request.user.osu_user_id

        leaderboard_id = request.data.get("leaderboard_id")
        invitee_id = request.data.get("user_id")

        # If no leaderboard_id was passed, raise 404
        if leaderboard_id is None or user_id is None:
            raise ParseError("Missing leaderboard_id or user_id parameter.")

        leaderboard = Leaderboard.objects.get(id=leaderboard_id)
        if not leaderboard.owner_id == user_id:
            raise PermissionDenied("Must be the leaderboard owner to perform this action.")
        
        if leaderboard.memberships.filter(user_id=invitee_id).exists():
            raise PermissionDenied("Cannot invite a user who is already a member.")

        message = request.data.get("message") or ""
        invite = Invite(user_id=invitee_id, leaderboard_id=leaderboard_id, message=message)
        invite.save()

        serialiser = InviteSerialiser(invite)
        return Response(serialiser.data)

class ListScores(APIView):
    """
    API endpoint for listing Scores on Memberships
    """
    queryset = Score.objects.distinct().order_by("-pp").select_related("beatmap").prefetch_related("user_stats", "user_stats__user").all()

    def get(self, request):
        leaderboard_id = request.query_params.get("leaderboard_id")
        user_id = request.query_params.get("user_id")
        beatmap_id = request.query_params.get("beatmap_id")
        
        # If no leaderboard_id was passed, raise 404
        if not leaderboard_id:
            raise ParseError("Missing leaderboard_id query parameter.")

        scores = self.queryset.filter(membership__leaderboard_id=leaderboard_id)
        if user_id:
            scores = scores.filter(membership__user_id=user_id)
            scores = scores.unique_maps()[:100]
        elif beatmap_id:
            scores = scores.filter(beatmap_id=beatmap_id)

        serialiser = ScoreSerialiser(scores, many=True)
        return Response(serialiser.data)
