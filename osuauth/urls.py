from django.urls import path, re_path
from django.conf.urls import url, include

from osuauth import views

urlpatterns = [
    path("test", views.test_view, name="test"),
    path("login", views.login_redirect, name="login_redirect"),
    path("callback", views.callback, name="callback")
]
