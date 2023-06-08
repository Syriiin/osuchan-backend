from http import HTTPStatus

import pytest
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse

from osuauth.views import login_redirect, stub_login_redirect


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
