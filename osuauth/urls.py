from django.urls import path, re_path
from django.conf.urls import url, include

from osuauth import views

urlpatterns = [
    path("login", views.login_redirect, name="login_redirect"),
    path("logout", views.logout_view, name="logout"),
    path("callback", views.callback, name="callback"),
    path("me", views.me)
]
