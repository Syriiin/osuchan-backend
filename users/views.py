from django.http import Http404
from rest_framework import permissions, status
from rest_framework.exceptions import NotAuthenticated, ParseError, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from common.osu.enums import Mods
from common.osu.utils import get_bitwise_mods, get_mod_acronyms
from leaderboards.models import Invite
from leaderboards.serialisers import UserInviteSerialiser
from osuauth.serialisers import UserSerialiser
from profiles.enums import AllowedBeatmapStatus
from profiles.models import ScoreFilter
from profiles.services import fetch_user
from profiles.tasks import update_user
from users.models import ScoreFilterPreset
from users.serialisers import ScoreFilterPresetSerialiser


class Me(APIView):
    """
    API Endpoint for checking the currently authenticated user
    """

    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get(self, request):
        # if user isn't logged in, 404
        if not request.user.is_authenticated:
            raise Http404

        # user might still not have osu_user if not they are a non-linked account (ie. admin)
        user = request.user
        if user.osu_user is not None:
            # TODO: specify gamemode based on user preferences
            if fetch_user(user.osu_user_id) is not None:
                update_user.delay(user.osu_user_id)

        serialiser = UserSerialiser(user)
        return Response(serialiser.data)


class MeScoreFilterPresetList(APIView):
    """
    API endpoint for listing ScoreFilterPresets for the currently authenticated user
    """

    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get(self, request):
        if not request.user.is_authenticated:
            raise Http404
        presets = ScoreFilterPreset.objects.select_related("score_filter").filter(
            user_id=request.user.id
        )
        serialiser = ScoreFilterPresetSerialiser(presets, many=True)
        return Response(serialiser.data)

    def post(self, request):
        if not request.user.is_authenticated:
            raise NotAuthenticated

        user_presets = ScoreFilterPreset.objects.filter(user=request.user)
        if user_presets.count() >= 100:
            raise PermissionDenied("Each user is limited to 100 presets.")

        name = request.data.get("name")
        if name is None:
            raise ParseError("Missing name parameter.")
        elif name == "":
            raise ParseError("Name cannot be blank.")

        score_filter_data = request.data.get("score_filter")
        if score_filter_data is None:
            raise ParseError("Missing score_filter parameter.")

        if "required_mods_json" in score_filter_data:
            required_mods_json = score_filter_data["required_mods_json"]
            required_mods = get_bitwise_mods(required_mods_json)
        else:
            required_mods = score_filter_data.get("required_mods", Mods.NONE)
            required_mods_json = get_mod_acronyms(required_mods)

        if "disqualified_mods_json" in score_filter_data:
            disqualified_mods_json = score_filter_data["disqualified_mods_json"]
            disqualified_mods = get_bitwise_mods(disqualified_mods_json)
        else:
            disqualified_mods = score_filter_data.get("disqualified_mods", Mods.NONE)
            disqualified_mods_json = get_mod_acronyms(disqualified_mods)

        score_filter_preset = ScoreFilterPreset.objects.create(
            name=name,
            user=request.user,
            score_filter=ScoreFilter.objects.create(
                allowed_beatmap_status=score_filter_data.get(
                    "allowed_beatmap_status", AllowedBeatmapStatus.RANKED_ONLY
                ),
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
                required_mods=required_mods,
                required_mods_json=required_mods_json,
                disqualified_mods=disqualified_mods,
                disqualified_mods_json=disqualified_mods_json,
                lowest_accuracy=score_filter_data.get("lowest_accuracy"),
                highest_accuracy=score_filter_data.get("highest_accuracy"),
                lowest_length=score_filter_data.get("lowest_length"),
                highest_length=score_filter_data.get("highest_length"),
            ),
        )

        serialiser = ScoreFilterPresetSerialiser(score_filter_preset)
        return Response(serialiser.data)


class MeScoreFilterPresetDetail(APIView):
    """
    API endpoint for getting ScoreFilterPresets for the currently authenticated user
    """

    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get(self, request, score_filter_preset_id):
        if not request.user.is_authenticated:
            raise Http404
        preset = ScoreFilterPreset.objects.select_related("score_filter").get(
            id=score_filter_preset_id
        )
        serialiser = ScoreFilterPresetSerialiser(preset)
        return Response(serialiser.data)

    def put(self, request, score_filter_preset_id):
        if not request.user.is_authenticated:
            raise NotAuthenticated

        name = request.data.get("name")
        if name is None:
            raise ParseError("Missing name parameter.")
        elif name == "":
            raise ParseError("Name cannot be blank.")

        score_filter_data = request.data.get("score_filter")
        if score_filter_data is None:
            raise ParseError("Missing score_filter parameter.")

        preset = ScoreFilterPreset.objects.select_related("score_filter").get(
            id=score_filter_preset_id
        )
        preset.name = name

        if "required_mods_json" in score_filter_data:
            required_mods_json = score_filter_data["required_mods_json"]
            required_mods = get_bitwise_mods(required_mods_json)
        else:
            required_mods = score_filter_data.get("required_mods", Mods.NONE)
            required_mods_json = get_mod_acronyms(required_mods)

        if "disqualified_mods_json" in score_filter_data:
            disqualified_mods_json = score_filter_data["disqualified_mods_json"]
            disqualified_mods = get_bitwise_mods(disqualified_mods_json)
        else:
            disqualified_mods = score_filter_data.get("disqualified_mods", Mods.NONE)
            disqualified_mods_json = get_mod_acronyms(disqualified_mods)

        score_filter = preset.score_filter
        score_filter.allowed_beatmap_status = score_filter_data.get(
            "allowed_beatmap_status", AllowedBeatmapStatus.RANKED_ONLY
        )
        score_filter.oldest_beatmap_date = score_filter_data.get("oldest_beatmap_date")
        score_filter.newest_beatmap_date = score_filter_data.get("newest_beatmap_date")
        score_filter.oldest_score_date = score_filter_data.get("oldest_score_date")
        score_filter.newest_score_date = score_filter_data.get("newest_score_date")
        score_filter.lowest_ar = score_filter_data.get("lowest_ar")
        score_filter.highest_ar = score_filter_data.get("highest_ar")
        score_filter.lowest_od = score_filter_data.get("lowest_od")
        score_filter.highest_od = score_filter_data.get("highest_od")
        score_filter.lowest_cs = score_filter_data.get("lowest_cs")
        score_filter.highest_cs = score_filter_data.get("highest_cs")
        score_filter.required_mods = required_mods
        score_filter.required_mods_json = required_mods_json
        score_filter.disqualified_mods = disqualified_mods
        score_filter.disqualified_mods_json = disqualified_mods_json
        score_filter.lowest_accuracy = score_filter_data.get("lowest_accuracy")
        score_filter.highest_accuracy = score_filter_data.get("highest_accuracy")
        score_filter.lowest_length = score_filter_data.get("lowest_length")
        score_filter.highest_length = score_filter_data.get("highest_length")

        score_filter.save()
        preset.save()

        serialiser = ScoreFilterPresetSerialiser(preset)
        return Response(serialiser.data)

    def delete(self, request, score_filter_preset_id):
        if not request.user.is_authenticated:
            raise Http404
        preset = ScoreFilterPreset.objects.get(
            id=score_filter_preset_id, user=request.user
        )
        preset.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeInviteList(APIView):
    """
    API endpoint for listing Invites for the currently authenticated user
    """

    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get(self, request):
        if not request.user.is_authenticated:
            raise Http404
        invites = Invite.objects.select_related(
            "leaderboard", "leaderboard__owner"
        ).filter(user_id=request.user.osu_user_id)
        serialiser = UserInviteSerialiser(invites, many=True)
        return Response(serialiser.data)
