import logging
import time

from celery import shared_task

from common.osu.beatmap_provider import BeatmapProvider
from common.osu.enums import BeatmapStatus, Gamemode
from leaderboards.models import Leaderboard
from leaderboards.tasks import update_memberships
from ppraces.tasks import update_pprace_players
from profiles.models import Beatmap
from profiles.services import (
    refresh_beatmaps_from_api,
    refresh_user_from_api,
    refresh_user_recent_from_api,
)

logger = logging.getLogger(__name__)


@shared_task(priority=1)
def dispatch_update_all_global_leaderboard_top_members(
    limit: int = 100, cooldown_seconds: int = 300
):
    """
    Dispatches update_user tasks for the top members of all global leaderboards
    """
    for leaderboard in Leaderboard.global_leaderboards.all():
        members = leaderboard.memberships.order_by("-pp")[:limit].values("user_id")

        for member in members:
            update_user.apply_async(
                kwargs={
                    "user_id": member["user_id"],
                    "gamemode": leaderboard.gamemode,
                    "cooldown_seconds": cooldown_seconds,
                },
                priority=4,
            )


@shared_task(priority=3)
def dispatch_update_community_leaderboard_members(
    leaderboard_id: int, limit: int = 100
):
    """
    Dispatches update_user tasks for all members of a given leaderboard
    """
    leaderboard = Leaderboard.community_leaderboards.get(id=leaderboard_id)
    members = leaderboard.memberships.order_by("-pp")[:limit].values("user_id")

    for member in members:
        update_user.apply_async(
            kwargs={
                "user_id": member["user_id"],
                "gamemode": leaderboard.gamemode,
            },
            priority=4,
        )


@shared_task(priority=7)
def update_user(
    user_id: int, gamemode: int = Gamemode.STANDARD, cooldown_seconds: int = 300
):
    """
    Runs an update for a given user
    """
    user_stats, updated = refresh_user_from_api(
        user_id=user_id, gamemode=Gamemode(gamemode), cooldown_seconds=cooldown_seconds
    )
    if user_stats is not None and updated:
        update_memberships.delay(
            user_id=user_stats.user_id, gamemode=user_stats.gamemode
        )
        update_pprace_players.delay(
            user_id=user_stats.user_id, gamemode=user_stats.gamemode
        )
    return user_stats


@shared_task(priority=7)
def update_user_by_username(username: str, gamemode: int = Gamemode.STANDARD):
    """
    Runs an update for a given user
    """
    user_stats, updated = refresh_user_from_api(
        username=username, gamemode=Gamemode(gamemode)
    )
    if user_stats is not None and updated:
        update_memberships.delay(
            user_id=user_stats.user_id, gamemode=user_stats.gamemode
        )
        update_pprace_players.delay(
            user_id=user_stats.user_id, gamemode=user_stats.gamemode
        )
    return user_stats


@shared_task(priority=8)
def update_user_recent(
    user_id: int, gamemode: int = Gamemode.STANDARD, cooldown_seconds: int = 60
):
    """
    Runs an update for a given user strictly for recent scores
    """
    user_stats, updated = refresh_user_recent_from_api(
        user_id=user_id, gamemode=Gamemode(gamemode), cooldown_seconds=cooldown_seconds
    )
    if user_stats is not None and updated:
        update_memberships.delay(
            user_id=user_stats.user_id, gamemode=user_stats.gamemode
        )
        update_pprace_players.delay(
            user_id=user_stats.user_id, gamemode=user_stats.gamemode
        )
    return user_stats


@shared_task(priority=0)
def update_loved_beatmaps():
    """
    Updates all loved beatmaps, cleaning up outdated data
    """
    for beatmap in Beatmap.objects.filter(status=BeatmapStatus.LOVED):
        logger.info(f"Sleeping for 100ms")
        # Sleep for 100ms to avoid rate limiting
        time.sleep(0.1)
        logger.info(f"Updating loved beatmap {beatmap.id}")
        beatmap = Beatmap.objects.get(id=beatmap.id)
        if beatmap.status != BeatmapStatus.LOVED:
            logger.warning(f"Beatmap {beatmap.id} is not loved")
            return None

        try:
            updated_beatmap = refresh_beatmaps_from_api([beatmap.id])[0]
        except IndexError:
            logger.info(
                f"Beatmap {beatmap.id} appears to have been unloved. Deleting..."
            )
            beatmap.delete()
            beatmap_provider = BeatmapProvider()
            beatmap_provider.delete_beatmap(str(beatmap.id))
            return None

        outdated_scores = updated_beatmap.scores.filter(
            date__lt=updated_beatmap.last_updated
        )
        if outdated_scores.count() > 0:
            logger.info(
                f"Deleting {outdated_scores.count()} outdated scores for beatmap {beatmap.id}"
            )
            outdated_scores.delete()
