from django.urls import path, include

from rest_framework import routers

from profiles import views

router = routers.DefaultRouter()
router.register(r"scores", views.ScoreViewSet)

urlpatterns = [
    path(r"", include(router.urls)),
    path(r"<user_string>/stats/<int:gamemode>", views.GetUserStats.as_view()),
    path(r"<user_string>/scores/<int:gamemode>", views.GetUserScores.as_view()),
    path(r"api-auth/", include("rest_framework.urls", namespace="rest_framework"))
]
