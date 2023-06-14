from django.urls import path, register_converter

from common.converters import GamemodeConverter, LeaderboardTypeConverter
from leaderboards import views

register_converter(GamemodeConverter, "gm")
register_converter(LeaderboardTypeConverter, "lb_type")

urlpatterns = [
    path(
        "<lb_type:leaderboard_type>/<gm:gamemode>",
        views.LeaderboardList.as_view(),
        name="leaderboard-list",
    ),
    path(
        "<lb_type:leaderboard_type>/<gm:gamemode>/<int:leaderboard_id>",
        views.LeaderboardDetail.as_view(),
        name="leaderboard-detail",
    ),
    path(
        "<lb_type:leaderboard_type>/<gm:gamemode>/<int:leaderboard_id>/scores",
        views.LeaderboardScoreList.as_view(),
        name="leaderboard-score-list",
    ),
    path(
        "<lb_type:leaderboard_type>/<gm:gamemode>/<int:leaderboard_id>/members",
        views.LeaderboardMemberList.as_view(),
        name="leaderboard-member-list",
    ),
    path(
        "<lb_type:leaderboard_type>/<gm:gamemode>/<int:leaderboard_id>/members/<int:user_id>",
        views.LeaderboardMemberDetail.as_view(),
        name="leaderboard-member-detail",
    ),
    path(
        "<lb_type:leaderboard_type>/<gm:gamemode>/<int:leaderboard_id>/invites",
        views.LeaderboardInviteList.as_view(),
        name="leaderboard-invite-list",
    ),
    path(
        "<lb_type:leaderboard_type>/<gm:gamemode>/<int:leaderboard_id>/invites/<int:user_id>",
        views.LeaderboardInviteDetail.as_view(),
        name="leaderboard-invite-detail",
    ),
    path(
        "<lb_type:leaderboard_type>/<gm:gamemode>/<int:leaderboard_id>/beatmaps/<int:beatmap_id>/scores",
        views.LeaderboardBeatmapScoreList.as_view(),
        name="leaderboard-beatmap-score-list",
    ),
    path(
        "<lb_type:leaderboard_type>/<gm:gamemode>/<int:leaderboard_id>/members/<int:user_id>/scores",
        views.LeaderboardMemberScoreList.as_view(),
        name="leaderboard-member-score-list",
    ),
]
