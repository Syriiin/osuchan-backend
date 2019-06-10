from django.urls import path, include

from profiles import views

urlpatterns = [
    path(r"stats/<user_string>/<int:gamemode>", views.GetUserStats.as_view()),
    path(r"scores", views.ListUserScores.as_view()),
    path(r"api-auth/", include("rest_framework.urls", namespace="rest_framework"))
]
