from django.urls import path, include

from leaderboards import views

urlpatterns = [
    path(r"leaderboards", views.ListLeaderboards.as_view()),
    path(r"leaderboards/<int:leaderboard_id>", views.GetLeaderboard.as_view()),
    path(r"members", views.ListMembers.as_view()),
    path(r"members/<int:user_id>", views.GetMember.as_view()),
    path(r"invites", views.ListInvites.as_view()),
    path(r"scores", views.ListScores.as_view())
]
