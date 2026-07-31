from datetime import datetime, timedelta, timezone

from celery import shared_task

from common.osu.enums import Gamemode
from minigames.enums import MinigameStatus
from minigames.models import Minigame, MinigamePlayer
from minigames.services import (
    finish_minigame,
    recompute_minigame,
    update_minigame_player_scores,
    update_minigame_status,
)


@shared_task(priority=2)
def dispatch_minigame_updates():
    """Dispatch update tasks for all active minigames."""
    minigames = Minigame.objects.filter(
        status__in=[
            MinigameStatus.WAITING_TO_START,
            MinigameStatus.IN_PROGRESS,
            MinigameStatus.FINALISING,
        ]
    )
    for minigame in minigames:
        update_minigame.delay(minigame_id=minigame.id)


@shared_task(priority=2)
def update_minigame(minigame_id: int):
    """Run a minigame state update."""
    minigame = Minigame.objects.get(id=minigame_id)

    if minigame.status == MinigameStatus.FINISHED:
        return

    assert minigame.status in [
        MinigameStatus.WAITING_TO_START,
        MinigameStatus.IN_PROGRESS,
        MinigameStatus.FINALISING,
    ], "Minigame must be in valid status for update"

    update_minigame_status(minigame)

    if minigame.status == MinigameStatus.IN_PROGRESS:
        win_reached = recompute_minigame(minigame)
        if win_reached:
            minigame.end_time = datetime.now(tz=timezone.utc)
            minigame.status = MinigameStatus.FINALISING
            minigame.save(update_fields=["end_time", "status"])
        else:
            trigger_minigame_player_updates(minigame_id=minigame.id)
    elif minigame.status == MinigameStatus.FINALISING:
        unfinalised_player_ids = minigame.get_unfinalised_players().values_list(
            "user_id", flat=True
        )

        if len(unfinalised_player_ids) > 0:
            # TODO: fix circular import
            from profiles.tasks import update_user_recent

            for user_id in unfinalised_player_ids:
                assert minigame.end_time is not None, "Minigame must have an end time"
                time_since_race_end = datetime.now(tz=timezone.utc) - minigame.end_time
                update_user_recent.apply_async(
                    kwargs={
                        "user_id": user_id,
                        "gamemode": minigame.gamemode,
                        "cooldown_seconds": time_since_race_end.total_seconds(),
                    },
                    priority=1,
                )
        else:
            finish_minigame(minigame)


@shared_task(priority=1)
def trigger_minigame_player_updates(minigame_id: int) -> None:
    """Dispatch score fetch tasks for players in a running minigame."""
    # TODO: fix circular import
    from profiles.tasks import update_user_recent

    minigame = Minigame.objects.get(id=minigame_id)
    for team in minigame.teams.all():
        if team.is_small_team():
            for player in team.players.all():
                update_user_recent.apply_async(
                    kwargs={
                        "user_id": player.user_id,
                        "gamemode": minigame.gamemode,
                        "cooldown_seconds": 30,
                    },
                    priority=1,
                )
            continue

        for player in team.players.all():
            user_stats = player.user.stats.filter(
                gamemode=minigame.gamemode,
            ).first()
            if user_stats is None:
                continue

            if user_stats.scores.filter(
                date__gte=datetime.now(tz=timezone.utc) - timedelta(minutes=10)
            ).exists():
                update_user_recent.apply_async(
                    kwargs={
                        "user_id": player.user_id,
                        "gamemode": minigame.gamemode,
                        "cooldown_seconds": 30,
                    },
                    priority=1,
                )
                continue

            if user_stats.last_updated < datetime.now(tz=timezone.utc) - timedelta(
                minutes=5
            ):
                update_user_recent.apply_async(
                    kwargs={
                        "user_id": player.user_id,
                        "gamemode": minigame.gamemode,
                        "cooldown_seconds": 30,
                    },
                    priority=1,
                )
                continue


@shared_task(priority=2)
def recompute_minigame_state(minigame_id: int) -> None:
    minigame = Minigame.objects.get(id=minigame_id)
    win_reached = recompute_minigame(minigame)
    if win_reached and minigame.status == MinigameStatus.IN_PROGRESS:
        minigame.end_time = datetime.now(tz=timezone.utc)
        minigame.status = MinigameStatus.FINALISING
        minigame.save(update_fields=["end_time", "status"])


@shared_task(priority=1)
def update_minigame_players_scores(user_id: int, gamemode=Gamemode.STANDARD):
    """
    Updates all minigame players for a given user and gamemode
    """
    players = MinigamePlayer.objects.filter(
        user_id=user_id,
        team__minigame__gamemode=gamemode,
        team__minigame__status__in=[
            MinigameStatus.IN_PROGRESS,
            MinigameStatus.FINALISING,
        ],
    ).select_related("team", "team__minigame")

    minigame_ids: set[int] = set()
    for player in players:
        update_minigame_player_scores(player)
        minigame_ids.add(player.team.minigame_id)

    for minigame_id in minigame_ids:
        recompute_minigame_state.delay(minigame_id=minigame_id)

    return players
