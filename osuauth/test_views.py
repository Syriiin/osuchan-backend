from collections import OrderedDict
from http import HTTPStatus
from unittest.mock import ANY

import pytest
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from freezegun import freeze_time

from osuauth.views import callback, login_redirect, stub_login_redirect


@pytest.mark.django_db
def test_login_redirect(rf, settings):
    settings.OSU_OAUTH_AUTHORISE_URL = "https://testurl"
    settings.OSU_OAUTH_SCOPE = "testscope"
    settings.OSU_CLIENT_REDIRECT_URI = "testredirecturl"
    settings.OSU_CLIENT_ID = "testclientid"

    url = reverse("login_redirect")
    request = rf.get(url)

    request.user = AnonymousUser()

    response = login_redirect(request)

    assert response.status_code == HTTPStatus.FOUND
    assert (
        response.url
        == "https://testurl?scope=testscope&response_type=code&redirect_uri=testredirecturl&client_id=testclientid"
    )


@pytest.mark.django_db
def test_stub_login_redirect(rf):
    url = reverse("login_redirect")
    request = rf.get(url)

    request.user = AnonymousUser()

    response = stub_login_redirect(request)

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == f"{reverse('callback')}?code=thisisafakecode"


@freeze_time("2023-01-01")
@pytest.mark.django_db
def test_callback(client):
    url = reverse("callback")
    response = client.get(url, {"code": "thisisafakecode"})

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == "/"

    response = client.get(reverse("me"))

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        "id": ANY,
        "date_joined": "2023-01-01T00:00:00Z",
        "is_beta_tester": False,
        "osu_user": {
            "id": 5701575,
            "username": "Syrin",
            "country": "AU",
            "join_date": "2015-01-20T20:45:29Z",
        },
    }
