from django.urls import path

from osuauth import views

urlpatterns = [
    path("login", views.login_redirect, name="login_redirect"),
    path("logout", views.logout_view, name="logout"),
    path("callback", views.callback, name="callback"),
]
