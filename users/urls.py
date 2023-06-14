from django.urls import path

from users import views

urlpatterns = [
    path("me", views.Me.as_view(), name="me"),
    path(
        "me/scorefilterpresets",
        views.MeScoreFilterPresetList.as_view(),
        name="me-score-filter-preset-list",
    ),
    path(
        "me/scorefilterpresets/<int:score_filter_preset_id>",
        views.MeScoreFilterPresetDetail.as_view(),
        name="me-score-filter-preset-detail",
    ),
    path("me/invites", views.MeInviteList.as_view(), name="me-invite-list"),
]
