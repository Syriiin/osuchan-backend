from django.conf import settings

import requests

from common.osu.enums import Gamemode
from osuauth.models import User
from profiles.models import OsuUser

class OsuBackend:
    """
    Authenticate against osu! OAuth
    """

    def authenticate(self, request, authorisation_code=None):
        # Exchange authorisation code for access and refresh tokens
        response = requests.post(settings.OSU_OAUTH_TOKEN_URL, data={
            "grant_type": "authorization_code",
            "client_id": settings.OSU_CLIENT_ID,
            "client_secret": settings.OSU_CLIENT_SECRET,
            "redirect_uri": settings.OSU_CLIENT_REDIRECT_URI,
            "code": authorisation_code
        })

        token_data = response.json()

        # Use new access token to get details about the osu user we are authing
        response = requests.get(settings.OSU_API_V2_BASE_URL + "me", headers={
            "Authorization": "{token_type} {access_token}".format(**token_data)
        })

        data = response.json()

        # create/update osu user object
        osu_user = OsuUser.objects.create_or_update(user_id=data["id"], gamemode=Gamemode.STANDARD)

        # create/find (auth) user, update and return
        try:
            # Try to get existing user from database
            user = User.objects.get(username=data["id"])
        except User.DoesNotExist:
            # User doesn't exist yet, so let's create it
            # We will use osu id as username to avoid name conflicts from name changes and such
            #   not a great solution but it's fine for now (could do something like require email input)
            user = User(username=data["id"])
        user.osu_user = osu_user
        user.save()

        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
