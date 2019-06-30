from rest_framework import permissions
from rest_framework.exceptions import ParseError
from rest_framework.views import APIView
from rest_framework.response import Response

from common.osu.enums import Mod
from profiles.models import Score
from profiles.serialisers import ScoreSerialiser
from leaderboards.models import Leaderboard, Membership
from leaderboards.serialisers import LeaderboardSerialiser, MembershipSerialiser
from leaderboards.services import create_leaderboard, create_membership
from leaderboards.enums import LeaderboardVisibility, AllowedBeatmapStatus

class ListLeaderboards(APIView):
    """
    API endpoint for listing Leaderboards
    """    
    queryset = Leaderboard.objects.all()

    def get(self, request):
        if request.user is not None:
            osu_user = request.user.osu_user
        else:
            osu_user = None
        leaderboards = self.queryset.visible_to(osu_user)
        serialiser = LeaderboardSerialiser(leaderboards, many=True)
        return Response(serialiser.data)

    def post(self, request):
        # Check required parameters
        if request.user is None:
            user_id = None
        else:
            user_id = request.user.osu_user_id

        gamemode = request.data.get("gamemode")
        if gamemode is None:
            raise ParseError("Missing gamemode parameter.")
        
        visibility = request.data.get("visibility")
        if visibility is None:
            raise ParseError("Missing visibility parameter.")
        elif visibility == LeaderboardVisibility.GLOBAL:
            raise ParseError("Parameter visibility must be either 1 for public, or 2 for private.")
        
        name = request.data.get("name")
        if name is None:
            raise ParseError("Missing name parameter.")
        
        leaderboard = Leaderboard(
            gamemode=gamemode,
            visibility=visibility,
            name=name
        )

        # Set optional score criteria
        leaderboard.allow_past_scores = request.data.get("allow_past_scores") or True
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

    def get(self, request, leaderboard_id):
        if request.user is not None:
            osu_user = request.user.osu_user
        else:
            osu_user = None
        leaderboard = self.queryset.visible_to(osu_user).get(id=leaderboard_id)
        serialiser = LeaderboardSerialiser(leaderboard)
        return Response(serialiser.data)

    def delete(self, request, leaderboard_id):
        leaderboard = self.queryset.get(id=leaderboard_id)
        return Response(leaderboard.delete())

class ListMembers(APIView):
    """
    API endpoint for listing Memberships
    """
    queryset = Membership.objects.select_related("user").all()

    def get(self, request):
        leaderboard_id = request.query_params.get("leaderboard_id")
        
        # If no leaderboard_id was passed, raise 404
        if not leaderboard_id:
            raise ParseError("Missing leaderboard_id query parameter.")

        memberships = self.queryset.filter(leaderboard_id=leaderboard_id)
        serialiser = MembershipSerialiser(memberships, many=True)
        return Response(serialiser.data)

    def post(self, request):
        leaderboard_id = request.data.get("leaderboard_id")
        user_id = request.data.get("user_id")

        # If no leaderboard_id was passed, raise 404
        if leaderboard_id is None:
            raise ParseError("Missing leaderboard_id parameter.")
        if user_id is None:
            raise ParseError("Missing user_id parameter.")

        membership = create_membership(leaderboard_id, user_id)
        serialiser = MembershipSerialiser(membership)
        return Response(serialiser.data)

class GetMember(APIView):
    """
    API endpoint for specific Members
    """
    queryset = Membership.objects.select_related("user").all()

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

class ListScores(APIView):
    """
    API endpoint for listing Scores on Memberships
    """
    queryset = Score.objects.select_related("beatmap").all()

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
        if beatmap_id:
            scores = scores.filter(beatmap_id=beatmap_id)
        serialiser = ScoreSerialiser(scores, many=True)
        return Response(serialiser.data)
