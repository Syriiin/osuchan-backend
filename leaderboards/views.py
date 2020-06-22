from django.core.paginator import Paginator

from rest_framework import permissions, status
from rest_framework.exceptions import ParseError, PermissionDenied, NotFound
from rest_framework.views import APIView
from rest_framework.response import Response

from common.utils import parse_int_or_none
from common.osu.enums import Mods, Gamemode
from osuauth.permissions import BetaPermission
from profiles.enums import ScoreSet
from profiles.models import Score, ScoreFilter
from profiles.serialisers import UserScoreSerialiser, BeatmapScoreSerialiser
from leaderboards.models import Leaderboard, Membership, Invite
from leaderboards.serialisers import LeaderboardSerialiser, LeaderboardMembershipSerialiser, UserMembershipSerialiser, LeaderboardInviteSerialiser, LeaderboardScoreSerialiser
from leaderboards.services import create_leaderboard, create_membership, delete_membership
from leaderboards.enums import LeaderboardAccessType

class ListLeaderboards(APIView):
    """
    API endpoint for listing Leaderboards
    """
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, BetaPermission)

    def get(self, request):
        osu_user_id = request.user.osu_user_id if request.user.is_authenticated else None

        gamemode = request.query_params.get("gamemode")
        if gamemode is None:
            raise ParseError("Missing gamemode parameter")
        leaderboard_type = request.query_params.get("type")
        if leaderboard_type is None:
            raise ParseError("Missing type parameter")
        page = parse_int_or_none(request.query_params.get("page"))

        if leaderboard_type == "global":
            leaderboards = Leaderboard.global_leaderboards.filter(gamemode=gamemode)
        elif leaderboard_type == "community":
            leaderboards = Leaderboard.community_leaderboards.filter(gamemode=gamemode).visible_to(osu_user_id).select_related("owner").order_by("-member_count")
            paginator = Paginator(leaderboards, 10)
            if page > paginator.num_pages:
                raise NotFound("Page does not exist")
            leaderboards = paginator.get_page(page)
        else:
            raise ParseError("Unknown value for type parameter.")

        serialiser = LeaderboardSerialiser(leaderboards, many=True)
        return Response(serialiser.data)

    def post(self, request):
        user_id = request.user.osu_user_id
        if user_id is None:
            raise PermissionDenied("Must be authenticated with an osu! account.")

        # Check required parameters
        gamemode = request.data.get("gamemode")
        if gamemode is None:
            raise ParseError("Missing gamemode parameter.")
        
        score_set = request.data.get("score_set")
        if score_set is None:
            raise ParseError("Missing score_set parameter.")
        elif gamemode != Gamemode.STANDARD:
            # score set is not supported yet by non-standard gamemodes since they dont support chokes
            score_set = ScoreSet.NORMAL
        
        access_type = request.data.get("access_type")
        if access_type is None:
            raise ParseError("Missing access_type parameter.")
        elif access_type == LeaderboardAccessType.GLOBAL:
            raise ParseError("Parameter access_type must be either 1 for public, 2 for invite-only public, or 3 for private.")
        
        name = request.data.get("name")
        if name is None:
            raise ParseError("Missing name parameter.")

        user_owned_leaderboards = Leaderboard.community_leaderboards.filter(owner_id=user_id)
        if user_owned_leaderboards.count() >= 10:
            raise PermissionDenied("Each user is limited to owning 10 leaderboards.")

        description = request.data.get("description")
        icon_url = request.data.get("icon_url")

        score_filter_data = request.data.get("score_filter")
        if score_filter_data is None:
            raise ParseError("Missing score_filter parameter.")
        
        leaderboard = Leaderboard(
            gamemode=gamemode,
            score_set=score_set,
            access_type=access_type,
            name=name,
            description=description or "",
            icon_url=icon_url or "",
            allow_past_scores=request.data.get("allow_past_scores"),
            score_filter=ScoreFilter(
                allowed_beatmap_status=score_filter_data.get("allowed_beatmap_status"),
                oldest_beatmap_date=score_filter_data.get("oldest_beatmap_date"),
                newest_beatmap_date=score_filter_data.get("newest_beatmap_date"),
                oldest_score_date=score_filter_data.get("oldest_score_date"),
                newest_score_date=score_filter_data.get("newest_score_date"),
                lowest_ar=score_filter_data.get("lowest_ar"),
                highest_ar=score_filter_data.get("highest_ar"),
                lowest_od=score_filter_data.get("lowest_od"),
                highest_od=score_filter_data.get("highest_od"),
                lowest_cs=score_filter_data.get("lowest_cs"),
                highest_cs=score_filter_data.get("highest_cs"),
                required_mods=score_filter_data.get("required_mods", Mods.NONE),
                disqualified_mods=score_filter_data.get("disqualified_mods", Mods.NONE),
                lowest_accuracy=score_filter_data.get("lowest_accuracy"),
                highest_accuracy=score_filter_data.get("highest_accuracy"),
                lowest_length=score_filter_data.get("lowest_length"),
                highest_length=score_filter_data.get("highest_length")
            )
        )
        
        # Hand off to create_leaderboard service to set relations, update owner membership, and save
        leaderboard = create_leaderboard(user_id, leaderboard)

        serialiser = LeaderboardSerialiser(leaderboard)
        return Response(serialiser.data)

class GetLeaderboard(APIView):
    """
    API endpoint for specific Leaderboards
    """
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, BetaPermission)

    def get(self, request, leaderboard_id):
        osu_user_id = request.user.osu_user_id if request.user.is_authenticated else None
        
        try:
            leaderboard = Leaderboard.objects.visible_to(osu_user_id).get(id=leaderboard_id)
        except Leaderboard.DoesNotExist:
            raise NotFound("Leaderboard not found.")

        serialiser = LeaderboardSerialiser(leaderboard)
        return Response(serialiser.data)

    def delete(self, request, leaderboard_id):
        user_id = request.user.osu_user_id
        if user_id is None:
            raise PermissionDenied("Must be authenticated with an osu! account.")

        try:
            leaderboard = Leaderboard.community_leaderboards.get(id=leaderboard_id)
        except Leaderboard.DoesNotExist:
            raise NotFound("Leaderboard not found.")
            
        if leaderboard.owner_id != user_id:
            raise PermissionDenied("Must be the leaderboard owner to perform this action.")

        leaderboard.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

class ListLeaderboardMembers(APIView):
    """
    API endpoint for listing Memberships
    """
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, BetaPermission)

    def get(self, request, leaderboard_id):
        memberships = Membership.objects.non_restricted().filter(leaderboard_id=leaderboard_id).select_related("user").order_by("-pp")
        serialiser = LeaderboardMembershipSerialiser(memberships[:100], many=True)
        return Response(serialiser.data)

    def post(self, request, leaderboard_id):
        user_id = request.user.osu_user_id
        if user_id is None:
            raise PermissionDenied("Must be authenticated with an osu! account.")
            
        membership = create_membership(leaderboard_id, user_id)
        serialiser = LeaderboardMembershipSerialiser(membership)
        return Response(serialiser.data)

class ListLeaderboardScores(APIView):
    """
    API endpoint for listing scores from all members of a leaderboard
    """
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, BetaPermission)

    def get(self, request, leaderboard_id):
        osu_user_id = request.user.osu_user_id if request.user.is_authenticated else None
        leaderboard = Leaderboard.objects.visible_to(osu_user_id).get(id=leaderboard_id)
        scores = Score.objects.non_restricted().distinct().filter(membership__leaderboard_id=leaderboard_id).select_related("user_stats", "user_stats__user", "beatmap").order_by("-pp", "date").get_score_set(score_set=leaderboard.score_set)
        serialiser = LeaderboardScoreSerialiser(scores[:5], many=True)
        return Response(serialiser.data)

class GetLeaderboardMember(APIView):
    """
    API endpoint for specific Members
    """
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, BetaPermission)

    def get(self, request, leaderboard_id, user_id):
        membership = Membership.objects.select_related("user").get(leaderboard_id=leaderboard_id, user_id=user_id)
        if membership.user.disabled:
            return None
        serialiser = LeaderboardMembershipSerialiser(membership)
        return Response(serialiser.data)

    def delete(self, request, leaderboard_id, user_id):
        if request.user.osu_user_id != user_id:
            raise PermissionDenied("You can only remove yourself from leaderboards.")
        delete_membership(leaderboard_id, user_id)
        return Response(status=status.HTTP_204_NO_CONTENT)

class ListLeaderboardInvites(APIView):
    """
    API endpoint for listing Invites for a Leaderboard
    """
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, BetaPermission)

    def get(self, request, leaderboard_id):
        invites = Invite.objects.filter(leaderboard_id=leaderboard_id).select_related("user")
        serialiser = LeaderboardInviteSerialiser(invites, many=True)
        return Response(serialiser.data)

    def post(self, request, leaderboard_id):
        user_id = request.user.osu_user_id
        if user_id is None:
            raise PermissionDenied("Must be authenticated with an osu! account.")
        
        leaderboard = Leaderboard.community_leaderboards.get(id=leaderboard_id)
        if not leaderboard.owner_id == user_id:
            raise PermissionDenied("Must be the leaderboard owner to perform this action.")

        invitee_ids = request.data.get("user_ids")
        message = request.data.get("message", "")

        invites = []
        for invitee_id in invitee_ids:
            if leaderboard.memberships.filter(user_id=invitee_id).exists():
                continue

            try:
                invite = Invite.objects.get(user_id=invitee_id, leaderboard_id=leaderboard_id)
            except Invite.DoesNotExist:
                invite = Invite(user_id=invitee_id, leaderboard_id=leaderboard_id, message=message)
                invite.save()
            
            invites.append(invite)

        serialiser = LeaderboardInviteSerialiser(invites, many=True)
        return Response(serialiser.data)

class GetLeaderboardInvite(APIView):
    """
    API endpoint for getting specific Invites
    """
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, BetaPermission)

    def get(self, request, leaderboard_id, user_id):
        invite = Invite.objects.select_related("user").get(leaderboard_id=leaderboard_id, user_id=user_id)
        serialiser = LeaderboardInviteSerialiser(invite)
        return Response(serialiser.data)

    def delete(self, request, leaderboard_id, user_id):
        invite = Invite.objects.get(leaderboard_id=leaderboard_id, user_id=user_id)
        invite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class ListLeaderboardBeatmapScores(APIView):
    """
    API endpoint for listing Scores on Beatmaps
    """
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, BetaPermission)

    def get(self, request, leaderboard_id, beatmap_id):
        osu_user_id = request.user.osu_user_id if request.user.is_authenticated else None
        leaderboard = Leaderboard.objects.visible_to(osu_user_id).get(id=leaderboard_id)
        scores = Score.objects.non_restricted().distinct().filter(membership__leaderboard_id=leaderboard_id, beatmap_id=beatmap_id).select_related("user_stats", "user_stats__user").order_by("-pp", "date").get_score_set(score_set=leaderboard.score_set)
        serialiser = BeatmapScoreSerialiser(scores[:50], many=True)
        return Response(serialiser.data)

class ListLeaderboardMemberScores(APIView):
    """
    API endpoint for listing Scores on Memberships
    """
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, BetaPermission)

    def get(self, request, leaderboard_id, user_id):
        osu_user_id = request.user.osu_user_id if request.user.is_authenticated else None
        leaderboard = Leaderboard.objects.visible_to(osu_user_id).get(id=leaderboard_id)
        scores = Score.objects.non_restricted().distinct().filter(membership__leaderboard_id=leaderboard_id, membership__user_id=user_id).select_related("beatmap").order_by("-pp", "date").get_score_set(score_set=leaderboard.score_set)
        serialiser = UserScoreSerialiser(scores[:100], many=True)
        return Response(serialiser.data)
