from celery import shared_task

from common.osu.enums import Gamemode
from leaderboards.models import Leaderboard
from profiles.services import refresh_user_from_api


@shared_task
def dispatch_update_all_global_leaderboard_top_members(limit: int = 100):
    """
    Dispatches update_user tasks for the top members of all global leaderboards
    """
    for leaderboard in Leaderboard.global_leaderboards.all():
        members = leaderboard.memberships.order_by("-pp")[:limit].values("user_id")

        for member in members:
            update_user.delay(member["user_id"], leaderboard.gamemode)


@shared_task
def dispatch_update_community_leaderboard_members(
    leaderboard_id: int, limit: int = 100
):
    """
    Dispatches update_user tasks for all members of a given leaderboard
    """
    leaderboard = Leaderboard.community_leaderboards.get(id=leaderboard_id)
    members = leaderboard.memberships.order_by("-pp")[:limit].values("user_id")

    for member in members:
        update_user.delay(member["user_id"], leaderboard.gamemode)


@shared_task
def update_user(user_id: int, gamemode: int = Gamemode.STANDARD):
    """
    Runs an update for a given user
    """
    refresh_user_from_api(user_id=user_id, gamemode=gamemode)
