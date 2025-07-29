from django.urls import path

from ppraces import views

urlpatterns = [
    path(
        "",
        views.PPRaceList.as_view(),
        name="leaderboard-list",
    ),
    path(
        "trigger-update",
        views.PPRacePlayerTriggerUpdate.as_view(),
        name="pprace-team-players-trigger-update",
    ),
    path(
        "<int:pprace_id>",
        views.PPRaceDetail.as_view(),
        name="pprace-detail",
    ),
    path(
        "<int:pprace_id>/start",
        views.PPRaceStart.as_view(),
        name="pprace-start",
    ),
    path(
        "<int:pprace_id>/recentscores",
        views.PPRaceRecentScoresList.as_view(),
        name="pprace-recent-scores-list",
    ),
    path(
        "<int:pprace_id>/teams/<int:team_id>/scores",
        views.PPRaceTeamScoresList.as_view(),
        name="pprace-team-scores-list",
    ),
]
