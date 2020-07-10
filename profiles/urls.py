from django.urls import path, register_converter

from common.converters import GamemodeConverter, LeaderboardTypeConverter
from profiles import views

register_converter(GamemodeConverter, "gm")
register_converter(LeaderboardTypeConverter, "lb_type")

urlpatterns = [
    path("users/<user_string>/stats/<gm:gamemode>", views.GetUserStats.as_view()),
    path("users/<int:user_id>/stats/<gm:gamemode>/scores", views.ListUserScores.as_view()),
    path("users/<int:user_id>/memberships/<lb_type:leaderboard_type>/<gm:gamemode>", views.ListUserMemberships.as_view()),
    path("beatmaps/<int:beatmap_id>", views.GetBeatmap.as_view())
]
