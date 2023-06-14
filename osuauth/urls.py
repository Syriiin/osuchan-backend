from django.conf import settings
from django.urls import path

from osuauth import views

if settings.USE_STUB_OSU_OAUTH:
    login_view = views.stub_login_redirect
else:
    login_view = views.login_redirect

urlpatterns = [
    path("login", login_view, name="login_redirect"),
    path("logout", views.logout_view, name="logout"),
    path("callback", views.callback, name="callback"),
]
