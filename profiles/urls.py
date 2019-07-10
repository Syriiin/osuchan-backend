from django.urls import path, include

from profiles import views

urlpatterns = [
    path(r"<user_string>/<int:gamemode>", views.GetUserStats.as_view()),
    path(r"<int:user_id>/<int:gamemode>/scores", views.ListUserScores.as_view()),
    path(r"beatmaps/<int:beatmap_id>", views.GetBeatmaps.as_view()),
    path(r"api-auth/", include("rest_framework.urls", namespace="rest_framework"))
]
