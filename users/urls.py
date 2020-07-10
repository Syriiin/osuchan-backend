from django.urls import path

from users import views

urlpatterns = [
    path("me", views.GetMe.as_view()),
    path("me/scorefilterpresets", views.ListScoreFilterPresets.as_view()),
    path("me/scorefilterpresets/<int:score_filter_preset_id>", views.GetScoreFilterPreset.as_view()),
    path("me/invites", views.ListInvites.as_view())
]
