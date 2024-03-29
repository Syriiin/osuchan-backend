from datetime import datetime

from celery import shared_task
from django.conf import settings
from django.db import transaction

from common.discord_webhook_sender import DiscordWebhookSender
from common.osu.enums import Gamemode, Mods
from common.osu.utils import (
    calculate_pp_total,
    get_gamemode_string_from_gamemode,
    get_mods_string,
)
from leaderboards.enums import LeaderboardAccessType
from leaderboards.models import Leaderboard, Membership
from leaderboards.utils import get_leaderboard_type_string_from_leaderboard_access_type
from profiles.enums import ScoreResult, ScoreSet
from profiles.models import Score, UserStats


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
    user_stats = UserStats.objects.get(user_id=user_id, gamemode=gamemode)

    for membership in memberships:
        leaderboard = membership.leaderboard
        if leaderboard.score_filter:
            scores = user_stats.scores.apply_score_filter(leaderboard.score_filter)
        else:
            scores = user_stats.scores.all()

        if not leaderboard.allow_past_scores:
            scores = scores.filter(date__gte=membership.join_date)

        scores = scores.get_score_set(score_set=leaderboard.score_set)

        membership.score_count = scores.count()

        if leaderboard.score_set == ScoreSet.NORMAL:
            membership.pp = calculate_pp_total(
                score.performance_total for score in scores
            )
        elif leaderboard.score_set == ScoreSet.NEVER_CHOKE:
            membership.pp = calculate_pp_total(
                score.nochoke_performance_total
                if score.result & ScoreResult.CHOKE
                else score.performance_total
                for score in scores
            )
        elif leaderboard.score_set == ScoreSet.ALWAYS_FULL_COMBO:
            membership.pp = calculate_pp_total(
                score.nochoke_performance_total for score in scores
            )

        membership.rank = (
            leaderboard.memberships.filter(pp__gt=membership.pp).count() + 1
        )

        if leaderboard.notification_discord_webhook_url != "":
            # Check for new top score
            pp_record = leaderboard.get_pp_record()
            player_top_score = scores.first()
            if (
                pp_record is not None
                and player_top_score is not None
                and player_top_score.performance_total > pp_record
            ):
                # NOTE: need to use a function with default params here so the closure has the correct variables
                def send_notification(
                    leaderboard_id=leaderboard.id,
                    score_id=player_top_score.id,
                ):
                    send_leaderboard_top_score_notification.delay(
                        leaderboard_id, score_id
                    )

                transaction.on_commit(send_notification)

            # Check for new top player
            leaderboard_top_player = leaderboard.get_top_membership()
            if (
                leaderboard_top_player is not None
                and leaderboard_top_player.user_id != membership.user_id
                and membership.rank == 1
                and membership.pp > 0
            ):
                # NOTE: need to use a function with default params here so the closure has the correct variables
                def send_notification(
                    leaderboard_id=leaderboard.id,
                    user_id=membership.user_id,
                ):
                    send_leaderboard_top_player_notification.delay(
                        leaderboard_id, user_id
                    )

                transaction.on_commit(send_notification)

        membership.scores.set(scores)

        membership.save()

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
    if score.mods != Mods.NONE:
        beatmap_details += f" +{get_mods_string(score.mods)}"

    if score.difficulty_total is not None:
        beatmap_details += f" **{score.difficulty_total:.2f} stars**"
    else:
        beatmap_details += (
            f" **{score.beatmap.difficulty_total:.2f} stars (without mods)**"
        )

    # TODO: fix this for nochoke leaderboards. pp will display wrong
    score_details = f"**{score.performance_total:.0f}pp** ({score.accuracy:.2f}%)"
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
                    "title": f"New pp record! ({score.performance_total:.0f}pp by {score.user_stats.user.username})",
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
