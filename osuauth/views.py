from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.http import Http404
from django.shortcuts import redirect


def login_redirect(request):
    """
    Endpoint for initiating osu authentication
    """
    if request.user.is_authenticated:
        # User is already logged in
        return redirect("/")

    return redirect(
        "{authorise_url}?scope={scope}&response_type=code&redirect_uri={redirect_uri}&client_id={client_id}".format(
            authorise_url=settings.OSU_OAUTH_AUTHORISE_URL,
            scope=settings.OSU_OAUTH_SCOPE,
            redirect_uri=settings.OSU_CLIENT_REDIRECT_URI,
            client_id=settings.OSU_CLIENT_ID,
        )
    )


def logout_view(request):
    logout(request)
    return redirect("/")


def callback(request):
    """
    Endpoint redirected to by osu oauth after user accepts or declines auth
    """
    error = request.GET.get("error", None)
    authorisation_code = request.GET.get("code", None)

    if error == "access_denied" or not authorisation_code:
        # User denied auth or something went wrong
        # TODO: error handle page
        return redirect("/")

    # User approved auth
    user = authenticate(request, authorisation_code=authorisation_code)

    if user is None:
        # authentication error, something bad probably happened because
        #   at this stage it's just between osuchan and osu to complete the auth
        # TODO: error handle page
        return redirect("/")

    login(request, user)

    return redirect("/")
