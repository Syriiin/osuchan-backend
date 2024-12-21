from collections import OrderedDict

from rest_framework import permissions
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from common.osu.enums import Gamemode, Mods
from common.osu.utils import get_json_mods, get_mod_acronyms
from common.utils import parse_float_or_none, parse_int_or_none
from leaderboards.models import Membership
from leaderboards.serialisers import UserMembershipSerialiser
from profiles.enums import AllowedBeatmapStatus, ScoreMutation, ScoreSet
from profiles.models import Beatmap, Score, ScoreFilter, UserStats
from profiles.serialisers import (
    BeatmapSerialiser,
    UserScoreSerialiser,
    UserStatsSerialiser,
)
from profiles.services import fetch_scores, fetch_user
from profiles.tasks import update_user, update_user_by_username


class UserStatsDetail(APIView):
    """
    API endpoint for getting UserStats
    """

    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get(self, request, user_string, gamemode):
        """
        Return UserStats based on a user_string and gamemode
        """
        user_id_type = request.query_params.get("user_id_type", "id")

        try:
            if user_id_type == "id":
                user_stats = fetch_user(user_id=int(user_string), gamemode=gamemode)
                if user_stats is None:
                    user_stats = update_user(
                        user_id=int(user_string), gamemode=gamemode
                    )
            elif user_id_type == "username":
                user_stats = fetch_user(username=user_string, gamemode=gamemode)
                if user_stats is None:
                    user_stats = update_user_by_username(
                        username=user_string, gamemode=gamemode
                    )
            else:
                raise NotFound("User not found.")

            if user_stats is None:
                raise NotFound("User not found.")

            update_user.delay(user_stats.user_id, gamemode)

            # Show not found for disabled (restricted) users
            if user_stats.user.disabled:
                raise NotFound("User not found.")
        except UserStats.DoesNotExist:
            raise NotFound("User not found.")

        serialiser = UserStatsSerialiser(user_stats)
        return Response(serialiser.data)


class BeatmapDetail(APIView):
    """
    API endpoint for getting Beatmaps
    """

    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

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


class UserScoreList(APIView):
    """
    API endpoint for Scores
    """

    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get(self, request, user_id, gamemode):
        """
        Return Scores based on a user_id, gamemode, score_set, and various filters
        """
        required_mods = parse_int_or_none(
            request.query_params.get("required_mods", Mods.NONE)
        )
        disqualified_mods = parse_int_or_none(
            request.query_params.get("disqualified_mods", Mods.NONE)
        )
        score_filter = ScoreFilter(
            allowed_beatmap_status=parse_int_or_none(
                request.query_params.get(
                    "allowed_beatmap_status", AllowedBeatmapStatus.RANKED_ONLY
                )
            ),
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
            required_mods=required_mods,
            required_mods_json=(
                get_mod_acronyms(required_mods) if required_mods is not None else []
            ),
            disqualified_mods=disqualified_mods,
            disqualified_mods_json=(
                get_mod_acronyms(disqualified_mods)
                if disqualified_mods is not None
                else []
            ),
            lowest_accuracy=parse_float_or_none(
                request.query_params.get("lowest_accuracy")
            ),
            highest_accuracy=parse_float_or_none(
                request.query_params.get("highest_accuracy")
            ),
            lowest_length=parse_float_or_none(
                request.query_params.get("lowest_length")
            ),
            highest_length=parse_float_or_none(
                request.query_params.get("highest_length")
            ),
        )
        score_set = parse_int_or_none(
            request.query_params.get("score_set", ScoreSet.NORMAL)
        )
        if gamemode != Gamemode.STANDARD:
            # score set is not supported yet by non-standard gamemodes since they dont support chokes
            score_set = ScoreSet.NORMAL

        scores = (
            Score.objects.select_related("beatmap")
            .non_restricted()
            .filter(user_stats__user_id=user_id, user_stats__gamemode=gamemode)
            .apply_score_filter(score_filter)
            .get_score_set(gamemode, score_set)
            .prefetch_related(
                "performance_calculations__performance_values",
                "performance_calculations__difficulty_calculation__difficulty_values",
            )
        )

        serialiser = UserScoreSerialiser(scores[:100], many=True)
        return Response(serialiser.data)

    def post(self, request, user_id, gamemode):
        """
        Add new Scores based on passes user_id, gamemode, beatmap_ids
        """
        scores = fetch_scores(user_id, request.data.get("beatmap_ids"), gamemode)
        scores = [score for score in scores if score.mutation == ScoreMutation.NONE]
        serialiser = UserScoreSerialiser(scores, many=True)
        return Response(serialiser.data)


class UserMembershipList(APIView):
    """
    API endpoint for listing Memberships for an OsuUser
    """

    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get(self, request, user_id, leaderboard_type, gamemode):
        osu_user_id = (
            request.user.osu_user_id if request.user.is_authenticated else None
        )

        limit = parse_int_or_none(request.query_params.get("limit", 5))
        offset = parse_int_or_none(request.query_params.get("offset", 0))
        if limit > 25:
            limit = 25

        if leaderboard_type == "global":
            memberships = Membership.global_memberships.filter(
                leaderboard__gamemode=gamemode, user_id=user_id
            ).order_by("rank")
        elif leaderboard_type == "community":
            memberships = (
                Membership.community_memberships.filter(
                    leaderboard__gamemode=gamemode, user_id=user_id
                )
                .visible_to(osu_user_id)
                .select_related("leaderboard", "leaderboard__owner")
                .order_by("-leaderboard__member_count")
            )

        serialiser = UserMembershipSerialiser(
            memberships[offset : offset + limit], many=True
        )
        return Response(OrderedDict(count=memberships.count(), results=serialiser.data))
