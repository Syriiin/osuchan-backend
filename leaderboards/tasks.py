from datetime import datetime

from celery import shared_task
from django.conf import settings
from django.db import transaction

from common.discord_webhook_sender import DiscordWebhookSender
from common.osu.enums import Gamemode, Mods
from common.osu.utils import (
    get_gamemode_string_from_gamemode,
    get_mods_string_from_json_mods,
)
from leaderboards.enums import LeaderboardAccessType
from leaderboards.models import Leaderboard, Membership
from leaderboards.services import update_membership
from leaderboards.utils import get_leaderboard_type_string_from_leaderboard_access_type
from profiles.enums import ScoreResult
from profiles.models import Score


@shared_task
@transaction.atomic
def update_memberships(user_id, gamemode=Gamemode.STANDARD):
    """
    Updates all non-archived memberships for a given user and gamemode
    """
    memberships = Membership.objects.select_related(
        "leaderboard", "leaderboard__score_filter"
    ).filter(
        user_id=user_id, leaderboard__gamemode=gamemode, leaderboard__archived=False
    )

    for membership in memberships:
        update_membership(membership.leaderboard, user_id)

    return memberships


@shared_task
def send_leaderboard_top_score_notification(leaderboard_id: int, score_id: int):
    # passing score_id instead of querying for top score in case it changes before the job is picked up

    leaderboard: Leaderboard = Leaderboard.objects.get(id=leaderboard_id)
    if leaderboard.notification_discord_webhook_url == "":
        return

    score: Score = Score.objects.get(id=score_id)

    leaderboard_link = f"{settings.FRONTEND_URL}/leaderboards/{get_leaderboard_type_string_from_leaderboard_access_type(leaderboard.access_type)}/{get_gamemode_string_from_gamemode(leaderboard.gamemode)}/{leaderboard.id}"

    beatmap_details = f"[{score.beatmap}](https://osu.ppy.sh/beatmapsets/{score.beatmap.set_id}#{get_gamemode_string_from_gamemode(score.beatmap.gamemode)}/{score.beatmap.id})"
    if len(score.mods_json) != 0:
        beatmap_details += f" +{get_mods_string_from_json_mods(score.mods_json)}"

    performance_calculation = score.get_performance_calculation()
    difficulty_total = (
        performance_calculation.difficulty_calculation.get_total_difficulty()
    )

    beatmap_details += f" **{difficulty_total:.2f} stars**"

    performance_calculation = score.get_performance_calculation()
    performance_total = performance_calculation.get_total_performance()
    score_details = f"**{performance_total:.0f}pp** ({score.accuracy:.2f}%)"
    if score.result is not None and score.result & ScoreResult.FULL_COMBO:
        score_details += " FC"
    else:
        score_details += (
            f" {score.best_combo}/{score.beatmap.max_combo} {score.count_miss}x misses"
        )

    discord_webhook_sender = DiscordWebhookSender()
    discord_webhook_sender.send(
        leaderboard.notification_discord_webhook_url,
        data={
            "content": None,
            "embeds": [
                {
                    "title": f"New pp record! ({performance_total:.0f}pp by {score.user_stats.user.username})",
                    "description": f"{leaderboard_link}",
                    "url": f"{leaderboard_link}",
                    "color": 3816140,  # #3A3ACC
                    "fields": [
                        {
                            "name": "Beatmap",
                            "value": beatmap_details,
                        },
                        {"name": "Score", "value": score_details},
                    ],
                    "author": {
                        "name": f"Leaderboard - {leaderboard.name}",
                        "url": f"{leaderboard_link}",
                        "icon_url": f"{leaderboard.icon_url}",
                    },
                    "timestamp": score.date.isoformat(),
                    "image": {
                        "url": f"https://assets.ppy.sh/beatmaps/{score.beatmap.set_id}/covers/cover.jpg"
                    },
                    "thumbnail": {
                        "url": f"https://a.ppy.sh/{score.user_stats.user_id}"
                    },
                }
            ],
            "username": "osu!chan",
            "avatar_url": f"{settings.FRONTEND_URL}/static/icon-128.png",
            "attachments": [],
        },
    )


@shared_task
def send_leaderboard_top_player_notification(leaderboard_id: int, user_id: int):
    # passing user_id instead of querying for top player in case it changes before the job is picked up

    leaderboard: Leaderboard = Leaderboard.objects.get(id=leaderboard_id)
    if leaderboard.notification_discord_webhook_url == "":
        return

    membership: Membership = leaderboard.memberships.get(user_id=user_id)

    if leaderboard.access_type == LeaderboardAccessType.GLOBAL:
        memberships = Membership.global_memberships
    else:
        memberships = Membership.community_memberships

    podium_memberships = (
        memberships.non_restricted()
        .filter(leaderboard_id=leaderboard_id)
        .select_related("user")
        .order_by("-pp")[:3]
    )

    leaderboard_link = f"{settings.FRONTEND_URL}/leaderboards/{get_leaderboard_type_string_from_leaderboard_access_type(leaderboard.access_type)}/{get_gamemode_string_from_gamemode(leaderboard.gamemode)}/{leaderboard.id}"

    discord_webhook_sender = DiscordWebhookSender()
    discord_webhook_sender.send(
        leaderboard.notification_discord_webhook_url,
        data={
            "content": None,
            "embeds": [
                {
                    "title": f"{membership.user.username} has reached #1!",
                    "description": f"{leaderboard_link}",
                    "url": f"{leaderboard_link}",
                    "color": 3816140,  # #3A3ACC
                    "fields": [
                        {
                            "name": f"#{i + 1} {m.user.username}",
                            "value": f"{m.pp:.0f}pp",
                            "inline": True,
                        }
                        for i, m in enumerate(podium_memberships)
                    ],
                    "author": {
                        "name": f"Leaderboard - {leaderboard.name}",
                        "url": f"{leaderboard_link}",
                        "icon_url": f"{leaderboard.icon_url}",
                    },
                    "timestamp": datetime.now().isoformat(),
                    "thumbnail": {"url": f"https://a.ppy.sh/{membership.user_id}"},
                }
            ],
            "username": "osu!chan",
            "avatar_url": f"{settings.FRONTEND_URL}/static/icon-128.png",
            "attachments": [],
        },
    )


@shared_task
def send_leaderboard_podium_notification(leaderboard_id: int):
    leaderboard: Leaderboard = Leaderboard.objects.get(id=leaderboard_id)
    if leaderboard.notification_discord_webhook_url == "":
        return

    if leaderboard.access_type == LeaderboardAccessType.GLOBAL:
        memberships = Membership.global_memberships
    else:
        memberships = Membership.community_memberships

    podium_memberships = (
        memberships.non_restricted()
        .filter(leaderboard_id=leaderboard_id)
        .select_related("user")
        .order_by("-pp")[:3]
    )

    leaderboard_link = f"{settings.FRONTEND_URL}/leaderboards/{get_leaderboard_type_string_from_leaderboard_access_type(leaderboard.access_type)}/{get_gamemode_string_from_gamemode(leaderboard.gamemode)}/{leaderboard.id}"

    discord_webhook_sender = DiscordWebhookSender()
    discord_webhook_sender.send(
        leaderboard.notification_discord_webhook_url,
        data={
            "content": None,
            "embeds": [
                {
                    "title": f"{leaderboard.name} current podium rankings",
                    "description": f"{leaderboard_link}",
                    "url": f"{leaderboard_link}",
                    "color": 3816140,  # #3A3ACC
                    "fields": [
                        {
                            "name": f"#{i + 1} {m.user.username}",
                            "value": f"{m.pp:.0f}pp",
                            "inline": True,
                        }
                        for i, m in enumerate(podium_memberships)
                    ],
                    "author": {
                        "name": f"Leaderboard - {leaderboard.name}",
                        "url": f"{leaderboard_link}",
                        "icon_url": f"{leaderboard.icon_url}",
                    },
                    "timestamp": datetime.now().isoformat(),
                    "thumbnail": {"url": leaderboard.icon_url},
                }
            ],
            "username": "osu!chan",
            "avatar_url": f"{settings.FRONTEND_URL}/static/icon-128.png",
            "attachments": [],
        },
    )
