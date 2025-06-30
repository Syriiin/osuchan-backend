from django.urls import path

from ppraces import views

urlpatterns = [
    path(
        "<int:pprace_id>",
        views.PPRaceDetail.as_view(),
        name="pprace-detail",
    ),
]
