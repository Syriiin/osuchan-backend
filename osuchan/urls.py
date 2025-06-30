from django.conf import settings
from django.conf.urls import include
from django.contrib import admin
from django.http import Http404, HttpResponse
from django.urls import path, register_converter

from common.converters import GamemodeConverter, LeaderboardTypeConverter
from common.osu.beatmap_provider import BeatmapNotFoundException, BeatmapProvider

register_converter(GamemodeConverter, "gm")
register_converter(LeaderboardTypeConverter, "lb_type")


def getBeatmapFile(request, beatmap_id):
    beatmap_provider = BeatmapProvider()
    try:
        beatmap_path = beatmap_provider.get_beatmap_file(beatmap_id)
    except BeatmapNotFoundException as e:
        raise Http404("beatmap does not exist")

    with open(beatmap_path, encoding="utf8") as fp:
        response = HttpResponse(fp.read())
        response["Content-Type"] = "text/plain"
        return response


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/users/", include("users.urls")),
    path("api/profiles/", include("profiles.urls")),
    path("api/leaderboards/", include("leaderboards.urls")),
    path("api/ppraces/", include("ppraces.urls")),
    path("osuauth/", include("osuauth.urls")),
    path("beatmapfiles/<int:beatmap_id>", getBeatmapFile),
    path("", include("django_prometheus.urls")),
]

# Enable debug toolbar in debug mode
if settings.DEBUG:
    import debug_toolbar

    urlpatterns.append(path("__debug__/", include(debug_toolbar.urls)))
