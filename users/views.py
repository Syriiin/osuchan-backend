from django.http import Http404

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import NotAuthenticated
from rest_framework import permissions

from common.osu.enums import Mods
from osuauth.serialisers import UserSerialiser
from osuauth.permissions import BetaPermission
from users.models import ScoreFilterPreset
from users.serialisers import ScoreFilterPresetSerialiser
from profiles.services import fetch_user
from profiles.models import ScoreFilter

class GetMe(APIView):
    """
    API Endpoint for checking the currently authenticated user
    """
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, BetaPermission)

    def get(self, request):
        # if user isn't logged in, 404
        if not request.user.is_authenticated:
            raise Http404

        # user might still not have osu_user if not they are a non-linked account (ie. admin)
        user = request.user
        if user.osu_user is not None:
            fetch_user(user_id=user.osu_user_id)    # TODO: specify gamemode based on user preferences

        serialiser = UserSerialiser(user)
        return Response(serialiser.data)

class ListScoreFilterPresets(APIView):
    """
    API endpoint for listing ScoreFilterPresets for the currently authenticated user
    """
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, BetaPermission)

    def get(self, request):
        if not request.user.is_authenticated:
            raise Http404
        presets = ScoreFilterPreset.objects.select_related("score_filter").filter(user_id=request.user.id)
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
        
        score_filter_preset = ScoreFilterPreset.objects.create(
            name=name,
            user=request.user,
            score_filter=ScoreFilter.objects.create(
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
                required_mods=score_filter_data.get("required_mods") if score_filter_data.get("required_mods") is not None else Mods.NONE,
                disqualified_mods=score_filter_data.get("disqualified_mods") if score_filter_data.get("disqualified_mods") is not None else Mods.NONE,
                lowest_accuracy=score_filter_data.get("lowest_accuracy"),
                highest_accuracy=score_filter_data.get("highest_accuracy")
            )
        )

        serialiser = ScoreFilterPresetSerialiser(score_filter_preset)
        return Response(serialiser.data)

class GetScoreFilterPreset(APIView):
    """
    API endpoint for getting ScoreFilterPresets for the currently authenticated user
    """
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, BetaPermission)

    def get(self, request, score_filter_preset_id):
        if not request.user.is_authenticated:
            raise Http404
        preset = ScoreFilterPreset.objects.select_related("score_filter").get(id=score_filter_preset_id)
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

        preset = ScoreFilterPreset.objects.select_related("score_filter").get(id=score_filter_preset_id)
        preset.name = name
        
        score_filter = preset.score_filter
        score_filter.allowed_beatmap_status = score_filter_data.get("allowed_beatmap_status")
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
        score_filter.required_mods = score_filter_data.get("required_mods") if score_filter_data.get("required_mods") is not None else Mods.NONE
        score_filter.disqualified_mods = score_filter_data.get("disqualified_mods") if score_filter_data.get("disqualified_mods") is not None else Mods.NONE
        score_filter.lowest_accuracy = score_filter_data.get("lowest_accuracy")
        score_filter.highest_accuracy = score_filter_data.get("highest_accuracy")

        score_filter.save()
        preset.save()

        serialiser = ScoreFilterPresetSerialiser(preset)
        return Response(serialiser.data)

    def delete(self, request, score_filter_preset_id):
        if not request.user.is_authenticated:
            raise Http404
        preset = ScoreFilterPreset.objects.get(id=score_filter_preset_id, user=request.user)
        return Response(preset.delete())
