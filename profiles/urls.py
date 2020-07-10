from django.urls import path, register_converter

from common.converters import GamemodeConverter, LeaderboardTypeConverter
from profiles import views

register_converter(GamemodeConverter, "gm")
register_converter(LeaderboardTypeConverter, "lb_type")

urlpatterns = [
    path(r"users/<user_string>/stats/<gm:gamemode>", views.GetUserStats.as_view()),
    path(r"users/<int:user_id>/stats/<gm:gamemode>/scores", views.ListUserScores.as_view()),
    path(r"users/<int:user_id>/memberships/<lb_type:leaderboard_type>/<gm:gamemode>", views.ListUserMemberships.as_view()),
    path(r"users/<int:user_id>/invites", views.ListUserInvites.as_view()),
    path(r"beatmaps/<int:beatmap_id>", views.GetBeatmap.as_view())
]
