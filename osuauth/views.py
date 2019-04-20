from django.shortcuts import render, redirect
from django.conf import settings
from django.urls import reverse
from django.contrib.auth import authenticate, login

import requests

def test_view(request):
    return render(request, "test.html")

def login_redirect(request):
    """
    Endpoint for initiating osu authentication
    """
    if request.user.is_authenticated:
        # User is already logged in
        return redirect("test")

    return redirect("{authorise_url}?scope={scope}&response_type=code&redirect_uri={redirect_uri}&client_id={client_id}".format(
        authorise_url=settings.OSU_OAUTH_AUTHORISE_URL,
        scope=settings.OSU_OAUTH_SCOPE,
        redirect_uri=settings.OSU_CLIENT_REDIRECT_URI,
        client_id=settings.OSU_CLIENT_ID
    ))

def callback(request):
    """
    Endpoint redirected to by osu oauth after user accepts or declines auth
    """
    error = request.GET.get("error", None)
    authorisation_code = request.GET.get("code", None)

    if error == "access_denied" or not authorisation_code:
        # User denied auth or something went wrong
        # TODO: error handle page
        return redirect("test")

    # User approved auth
    user = authenticate(request, authorisation_code=authorisation_code)
    
    if user is None:
        # authentication error, something bad probably happened because
        #   at this state it's just between osuchan and osu to complete the auth
        # TODO: error handle page
        return redirect("test")

    login(request, user)

    return redirect("test")
