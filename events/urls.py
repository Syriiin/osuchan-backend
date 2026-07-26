from django.urls import path

from events import views

urlpatterns = [
    path("", views.EventList.as_view(), name="event-list"),
    path("<slug:slug>", views.EventDetail.as_view(), name="event-detail"),
    path(
        "<slug:slug>/attendees",
        views.EventAttendeeList.as_view(),
        name="event-attendee-list",
    ),
    path(
        "<slug:slug>/attendees/<int:user_id>",
        views.EventAttendeeDetail.as_view(),
        name="event-attendee-detail",
    ),
    path(
        "<slug:slug>/leaderboards",
        views.EventLeaderboardList.as_view(),
        name="event-leaderboard-list",
    ),
    path(
        "<slug:slug>/leaderboards/<int:event_leaderboard_id>",
        views.EventLeaderboardDetail.as_view(),
        name="event-leaderboard-detail",
    ),
    path(
        "<slug:slug>/challenges",
        views.BeatmapChallengeList.as_view(),
        name="beatmap-challenge-list",
    ),
    path(
        "<slug:slug>/challenges/<int:challenge_id>/scores",
        views.BeatmapChallengeScoreList.as_view(),
        name="beatmap-challenge-score-list",
    ),
]
