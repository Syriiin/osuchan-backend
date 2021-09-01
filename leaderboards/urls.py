from django.urls import path, register_converter

from common.converters import GamemodeConverter, LeaderboardTypeConverter
from leaderboards import views

register_converter(GamemodeConverter, "gm")
register_converter(LeaderboardTypeConverter, "lb_type")

urlpatterns = [
    path("<lb_type:leaderboard_type>/<gm:gamemode>", views.ListLeaderboards.as_view()),
    path(
        "<lb_type:leaderboard_type>/<gm:gamemode>/<int:leaderboard_id>",
        views.GetLeaderboard.as_view(),
    ),
    path(
        "<lb_type:leaderboard_type>/<gm:gamemode>/<int:leaderboard_id>/scores",
        views.ListLeaderboardScores.as_view(),
    ),
    path(
        "<lb_type:leaderboard_type>/<gm:gamemode>/<int:leaderboard_id>/members",
        views.ListLeaderboardMembers.as_view(),
    ),
    path(
        "<lb_type:leaderboard_type>/<gm:gamemode>/<int:leaderboard_id>/members/<int:user_id>",
        views.GetLeaderboardMember.as_view(),
    ),
    path(
        "<lb_type:leaderboard_type>/<gm:gamemode>/<int:leaderboard_id>/invites",
        views.ListLeaderboardInvites.as_view(),
    ),
    path(
        "<lb_type:leaderboard_type>/<gm:gamemode>/<int:leaderboard_id>/invites/<int:user_id>",
        views.GetLeaderboardInvite.as_view(),
    ),
    path(
        "<lb_type:leaderboard_type>/<gm:gamemode>/<int:leaderboard_id>/beatmaps/<int:beatmap_id>/scores",
        views.ListLeaderboardBeatmapScores.as_view(),
    ),
    path(
        "<lb_type:leaderboard_type>/<gm:gamemode>/<int:leaderboard_id>/members/<int:user_id>/scores",
        views.ListLeaderboardMemberScores.as_view(),
    ),
]
