from datetime import datetime, timedelta

import pytz
from django.db import transaction

from common.osu import apiv1
from common.osu.enums import Gamemode
from profiles.models import UserStats
from profiles.tasks import update_user


def fetch_user(user_id=None, username=None, gamemode=Gamemode.STANDARD):
    """
    Fetch user from database and enqueue update (max once each 5 minutes)
    """
    # Check for invalid inputs
    if not user_id and not username:
        raise ValueError("Must pass either username or user_id")

    # Attempt to get the UserStats model and enqueue update
    try:
        if user_id:
            user_stats = UserStats.objects.select_related("user").get(
                user_id=user_id, gamemode=gamemode
            )
        else:
            user_stats = UserStats.objects.select_related("user").get(
                user__username__iexact=username, gamemode=gamemode
            )

        if user_stats.last_updated < (
            datetime.utcnow().replace(tzinfo=pytz.UTC) - timedelta(minutes=5)
        ):
            # User was last updated more than 5 minutes ago, so enqueue another update
            update_user.delay(user_id=user_stats.user_id, gamemode=gamemode)
    except UserStats.DoesNotExist:
        # User not in database, either doesn't exist or is first time seeing this user (or namechange)
        # Calling update_user in a blocking way here because otherwise we would be showing the user to not exist, before we know that for sure
        # TODO: maybe get rid of this in favor of some sort of realtime update progress display to the user via websockets observing celery events
        user_stats = update_user(user_id=user_id, username=username, gamemode=gamemode)

    return user_stats


@transaction.atomic
def fetch_scores(user_id, beatmap_ids, gamemode):
    """
    Fetch and add scores for a user on beatmaps in a gamemode
    """
    # Fetch UserStats from database
    user_stats = UserStats.objects.select_for_update().get(
        user_id=user_id, gamemode=gamemode
    )

    full_score_data_list = []
    for beatmap_id in beatmap_ids:
        # Fetch score data from osu api
        score_data_list = apiv1.get_scores(
            beatmap_id=beatmap_id, user_id=user_id, gamemode=int(gamemode)
        )

        # Add beatmap id to turn it into the common json format
        for score_data in score_data_list:
            score_data["beatmap_id"] = beatmap_id

        full_score_data_list += score_data_list

    # Process add scores
    new_scores = user_stats.add_scores_from_data(full_score_data_list)

    return new_scores
