from django.urls import path

from profiles import views

urlpatterns = [
    path(
        "users/<user_string>/stats/<gm:gamemode>",
        views.UserStatsDetail.as_view(),
        name="user-stats-detail",
    ),
    path(
        "users/<int:user_id>/stats/<gm:gamemode>/scores",
        views.UserScoreList.as_view(),
        name="user-score-list",
    ),
    path(
        "users/<int:user_id>/memberships/<lb_type:leaderboard_type>/<gm:gamemode>",
        views.UserMembershipList.as_view(),
        name="user-membership-list",
    ),
    path(
        "beatmaps/<int:beatmap_id>",
        views.BeatmapDetail.as_view(),
        name="beatmap-detail",
    ),
]
