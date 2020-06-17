from django.urls import path, include

from leaderboards import views

urlpatterns = [
    path(r"leaderboards", views.ListLeaderboards.as_view()),
    path(r"leaderboards/<int:leaderboard_id>", views.GetLeaderboard.as_view()),
    path(r"leaderboards/<int:leaderboard_id>/members", views.ListLeaderboardMembers.as_view()),
    path(r"leaderboards/<int:leaderboard_id>/scores", views.ListLeaderboardScores.as_view()),
    path(r"leaderboards/<int:leaderboard_id>/members/<int:user_id>", views.GetLeaderboardMember.as_view()),
    path(r"leaderboards/<int:leaderboard_id>/invites", views.ListLeaderboardInvites.as_view()),
    path(r"leaderboards/<int:leaderboard_id>/invites/<int:user_id>", views.GetLeaderboardInvite.as_view()),
    path(r"leaderboards/<int:leaderboard_id>/beatmaps/<int:beatmap_id>/scores", views.ListLeaderboardBeatmapScores.as_view()),
    path(r"leaderboards/<int:leaderboard_id>/members/<int:user_id>/scores", views.ListLeaderboardMemberScores.as_view())
]
