from datetime import datetime

from django.db import transaction

from common.osu.utils import calculate_pp_total
from ppraces.enums import PPRaceStatus
from ppraces.models import PPRace, PPRacePlayer, PPRaceScore, PPRaceTeam
from profiles.enums import ScoreSet
from profiles.models import Score


@transaction.atomic
def update_pprace_status(pprace: PPRace) -> PPRace:
    """
    Update the status of a pp race
    """
    if pprace.start_time > datetime.now():
        pprace.status = PPRaceStatus.WAITING
    elif pprace.end_time < datetime.now():
        pprace.status = PPRaceStatus.FINISHED
        # TODO: trigger final update for all players and teams
    else:
        pprace.status = PPRaceStatus.IN_PROGRESS

    pprace.save()
    return pprace


@transaction.atomic
def update_pprace_team(team: PPRaceTeam) -> PPRaceTeam:
    """
    Update the total pp and score count of a team
    """
    pprace_scores = PPRaceScore.objects.filter(team_id=team.id)
    scores = Score.objects.filter(
        id__in=pprace_scores.values_list("score_id", flat=True),
    ).get_score_set()

    team.total_pp = calculate_pp_total(
        pp for pp in scores.values_list("performance_total", flat=True)
    )
    team.score_count = scores.count()

    team.save()
    return team


@transaction.atomic
def update_pprace_player(player: PPRacePlayer) -> PPRacePlayer:
    """
    Update a single pp race player
    """
    team = player.team
    pprace = team.pprace

    scores = Score.objects.filter(
        user_id=player.user_id,
        gamemode=pprace.gamemode,
        date__gte=pprace.start_time,
        date__lte=pprace.end_time,
    ).get_score_set(
        gamemode=pprace.gamemode,
        score_set=ScoreSet.NORMAL,
        calculator_engine=pprace.calculator_engine,
        primary_performance_value=pprace.primary_performance_value,
    )

    pprace_scores = [
        PPRaceScore(
            score=score,
            player=player,
            team=team,
            performance_total=score.performance_total,
        )
        for score in scores
        # Skip scores missing performance calculation
        if score.performance_total is not None
    ]

    PPRaceScore.objects.bulk_create(
        pprace_scores,
        update_conflicts=True,
        update_fields=["performance_total"],
        unique_fields=["player_id", "score_id"],
    )

    outdated_pprace_scores = PPRaceScore.objects.filter(player=player).exclude(
        score_id__in=[score.id for score in scores]
    )
    outdated_pprace_scores.delete()

    player.score_count = len(pprace_scores)
    player.pp = calculate_pp_total(score.performance_total for score in pprace_scores)

    player.save()

    return player
