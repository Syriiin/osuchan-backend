from django.urls import path, include

from profiles import views

urlpatterns = [
    path(r"users/<user_string>/stats/<int:gamemode>", views.GetUserStats.as_view()),
    path(r"users/<int:user_id>/stats/<int:gamemode>/scores", views.ListUserScores.as_view()),
    path(r"users/<int:user_id>/invites", views.ListUserInvites.as_view()),
    path(r"beatmaps/<int:beatmap_id>", views.GetBeatmaps.as_view())
]
