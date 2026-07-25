from django.urls import path

from minigames import views

urlpatterns = [
    path("", views.MinigameList.as_view(), name="minigame-list"),
    path("history", views.MinigameHistoryList.as_view(), name="minigame-history"),
    path("<int:game_id>", views.MinigameDetail.as_view(), name="minigame-detail"),
    path("<int:game_id>/start", views.MinigameStart.as_view(), name="minigame-start"),
    path(
        "<int:game_id>/recent-scores",
        views.MinigameRecentScoresList.as_view(),
        name="minigame-recent-scores",
    ),
    path(
        "<int:game_id>/scoring-scores",
        views.MinigameScoringScoresList.as_view(),
        name="minigame-scoring-scores",
    ),
    path("<int:game_id>/join", views.MinigameJoin.as_view(), name="minigame-join"),
    path("<int:game_id>/leave", views.MinigameLeave.as_view(), name="minigame-leave"),
    path(
        "<int:game_id>/settings",
        views.MinigameUpdateSettings.as_view(),
        name="minigame-settings",
    ),
    path(
        "<int:game_id>/move-team",
        views.MinigameMoveTeam.as_view(),
        name="minigame-move-team",
    ),
]
