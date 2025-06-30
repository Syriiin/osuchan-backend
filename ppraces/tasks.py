from celery import shared_task

from common.osu.enums import Gamemode
from ppraces.enums import PPRaceStatus
from ppraces.models import PPRace, PPRacePlayer
from ppraces.services import (
    update_pprace_player,
    update_pprace_status,
    update_pprace_team,
)


@shared_task(priority=8)
def dispatch_update_all_ppraces():
    """
    Dispatch update tasks for all pp races
    """
    ppraces = PPRace.objects.filter(
        status__in=[PPRaceStatus.IN_PROGRESS, PPRaceStatus.WAITING_TO_START]
    )
    for pprace in ppraces:
        update_pprace.delay(pprace_id=pprace.id)


@shared_task(priority=8)
def update_pprace(pprace_id: int):
    """
    Update state of a pp race
    """
    pprace = PPRace.objects.get(id=pprace_id)
    update_pprace_status(pprace)

    # TODO: fix circular import

    if pprace.status == PPRaceStatus.IN_PROGRESS:
        from profiles.tasks import update_user_recent

        for team in pprace.teams.all():
            for player in team.players.all():

                update_user_recent.delay(
                    user_id=player.user_id, gamemode=pprace.gamemode
                )


@shared_task(priority=8)
def update_pprace_players(user_id, gamemode=Gamemode.STANDARD):
    """
    Updates all pp race players for a given user and gamemode
    """
    players = PPRacePlayer.objects.filter(
        user_id=user_id,
        team__pprace__gamemode=gamemode,
        team__pprace__status=PPRaceStatus.IN_PROGRESS,
    ).select_related("team", "team__pprace")

    for player in players:
        update_pprace_player(player)
        update_pprace_team(player.team)

    return players
