from django.contrib import admin
from django.urls import path, re_path
from django.conf import settings
from django.conf.urls import include

from main.views import main, getBeatmapFile

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/users/", include("users.urls")),
    path("api/profiles/", include("profiles.urls")),
    path("api/leaderboards/", include("leaderboards.urls")),
    path("osuauth/", include("osuauth.urls")),
    path("beatmapfiles/<int:beatmap_id>", getBeatmapFile)
]

# Enable debug toolbar in debug mode
if settings.DEBUG:
    import debug_toolbar
    urlpatterns.append(
        path('__debug__/', include(debug_toolbar.urls))
    )

urlpatterns.append(
    re_path(r"^.*", main, name="main")
)
