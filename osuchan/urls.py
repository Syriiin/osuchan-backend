from django.conf import settings
from django.conf.urls import include
from django.contrib import admin
from django.http import HttpResponse
from django.urls import path

from common.utils import get_beatmap_path


def getBeatmapFile(request, beatmap_id):
    with open(get_beatmap_path(beatmap_id), encoding="utf8") as fp:
        response = HttpResponse(fp.read())
        response["Content-Type"] = "text/plain"
        return response


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/users/", include("users.urls")),
    path("api/profiles/", include("profiles.urls")),
    path("api/leaderboards/", include("leaderboards.urls")),
    path("osuauth/", include("osuauth.urls")),
    path("beatmapfiles/<int:beatmap_id>", getBeatmapFile),
]

# Enable debug toolbar in debug mode
if settings.DEBUG:
    import debug_toolbar

    urlpatterns.append(path("__debug__/", include(debug_toolbar.urls)))
