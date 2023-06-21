from datetime import datetime

import requests
from django.conf import settings
from django.db import transaction

from leaderboards.models import Leaderboard, Membership
from osuauth.models import User
from profiles.models import OsuUser


@transaction.atomic
def create_or_update_osu_user(
    id: int, username: str, country_code: str, join_date: datetime
):
    try:
        osu_user = OsuUser.objects.select_for_update().get(id=id)
    except OsuUser.DoesNotExist:
        osu_user = OsuUser(id=id)

        # Create memberships with global leaderboards
        global_leaderboards = Leaderboard.global_leaderboards.values("id")
        # TODO: refactor this to be somewhere else. dont really like setting values to 0
        global_memberships = [
            Membership(
                leaderboard_id=leaderboard["id"],
                user_id=osu_user.id,
                pp=0,
                rank=0,
                score_count=0,
            )
            for leaderboard in global_leaderboards
        ]
        Membership.objects.bulk_create(global_memberships)

    # Update OsuUser fields
    osu_user.username = username
    osu_user.country = country_code
    osu_user.join_date = join_date
    osu_user.disabled = False

    osu_user.save()

    return osu_user


def create_or_update_django_user(osu_user: OsuUser):
    try:
        # Try to get existing user from database
        user = User.objects.get(username=osu_user.id)
    except User.DoesNotExist:
        # User doesn't exist yet, so let's create it
        # We will use osu id as username to avoid name conflicts from name changes and such
        #   not a great solution but it's fine for now (could do something like require email input)
        user = User(username=osu_user.id)

    user.osu_user = osu_user

    user.save()

    return user


class OsuBackend:
    """
    Authenticate against osu! OAuth
    """

    def authenticate(self, request, authorisation_code=None):
        # Exchange authorisation code for access and refresh tokens
        response = requests.post(
            settings.OSU_OAUTH_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "client_id": settings.OSU_CLIENT_ID,
                "client_secret": settings.OSU_CLIENT_SECRET,
                "redirect_uri": settings.OSU_CLIENT_REDIRECT_URI,
                "code": authorisation_code,
            },
        )

        response.raise_for_status()

        token_data = response.json()

        # Use new access token to get details about the osu user we are authing
        response = requests.get(
            settings.OSU_API_V2_BASE_URL + "me",
            headers={
                "Authorization": "{token_type} {access_token}".format(**token_data)
            },
        )

        data = response.json()

        osu_user = create_or_update_osu_user(
            data["id"],
            data["username"],
            data["country"]["code"],
            datetime.strptime(data["join_date"], "%Y-%m-%dT%H:%M:%S%z"),
        )

        user = create_or_update_django_user(osu_user)

        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


# TODO: replace with stub of osu v2 api
class StubOsuBackend:
    """
    Pretend to authenticate against osu! OAuth
    """

    def authenticate(self, request, authorisation_code=None):
        osu_user = create_or_update_osu_user(
            5701575,
            "Syrin",
            "AU",
            datetime.strptime("2015-01-20T20:45:29+00:00", "%Y-%m-%dT%H:%M:%S%z"),
        )

        user = create_or_update_django_user(osu_user)

        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
