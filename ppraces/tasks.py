from datetime import datetime, timedelta, timezone

from celery import shared_task

from common.osu.enums import Gamemode
from ppraces.enums import PPRaceStatus
from ppraces.models import PPRace, PPRacePlayer
from ppraces.services import (
    update_pprace_player,
    update_pprace_status,
    update_pprace_team,
)
from profiles.models import UserStats


@shared_task(priority=8)
def dispatch_update_all_ppraces():
    """
    Dispatch update tasks for all pp races
    """
    ppraces = PPRace.objects.filter(
        status__in=[
            PPRaceStatus.WAITING_TO_START,
            PPRaceStatus.IN_PROGRESS,
            PPRaceStatus.FINALISING,
        ]
    )
    for pprace in ppraces:
        update_pprace.delay(pprace_id=pprace.id)


@shared_task(priority=8)
def update_pprace(pprace_id: int):
    """
    Update state of a pp race
    """
    pprace = PPRace.objects.get(id=pprace_id)

    assert pprace.status in [
        PPRaceStatus.WAITING_TO_START,
        PPRaceStatus.IN_PROGRESS,
        PPRaceStatus.FINALISING,
    ], "PPRace must be in a valid status for update"

    update_pprace_status(pprace)

    # TODO: fix circular import
    from profiles.tasks import update_user_recent

    if pprace.status == PPRaceStatus.IN_PROGRESS:
        for team in pprace.teams.all():
            update_pprace_team(team)

            if team.is_small_team():
                for player in team.players.all():
                    update_user_recent.apply_async(
                        kwargs={
                            "user_id": player.user_id,
                            "gamemode": pprace.gamemode,
                            "cooldown_seconds": 30,
                        },
                        priority=9,
                    )
                continue

            for player in team.players.all():
                user_stats = player.user.stats.get(
                    gamemode=pprace.gamemode,
                )
                if user_stats is None:
                    continue

                if user_stats.scores.filter(
                    date__gte=datetime.now(tz=timezone.utc) - timedelta(minutes=10)
                ).exists():
                    update_user_recent.delay(
                        user_id=player.user_id,
                        gamemode=pprace.gamemode,
                        cooldown_seconds=30,
                    )
                    continue

                if user_stats.last_updated < datetime.now(tz=timezone.utc) - timedelta(
                    minutes=5
                ):
                    update_user_recent.delay(
                        user_id=player.user_id, gamemode=pprace.gamemode
                    )
                    continue
    elif pprace.status == PPRaceStatus.FINALISING:
        for team in pprace.teams.all():
            update_pprace_team(team)

        unfinalised_player_ids = pprace.get_unfinalised_players().values_list(
            "user_id", flat=True
        )

        for user_id in unfinalised_player_ids:
            assert pprace.end_time is not None, "PPRace must have an end time"
            time_since_race_end = datetime.now(tz=timezone.utc) - pprace.end_time
            update_user_recent.apply_async(
                kwargs={
                    "user_id": user_id,
                    "gamemode": pprace.gamemode,
                    "cooldown_seconds": time_since_race_end.total_seconds(),
                },
                priority=9,
            )


@shared_task(priority=8)
def update_pprace_players(user_id, gamemode=Gamemode.STANDARD):
    """
    Updates all pp race players for a given user and gamemode
    """
    players = PPRacePlayer.objects.filter(
        user_id=user_id,
        team__pprace__gamemode=gamemode,
        team__pprace__status__in=[PPRaceStatus.IN_PROGRESS, PPRaceStatus.FINALISING],
    ).select_related("team", "team__pprace")

    for player in players:
        update_pprace_player(player)
        if player.team.is_small_team():
            update_pprace_team(player.team)

    return players
