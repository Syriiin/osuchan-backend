from datetime import datetime, timezone

from django.db import transaction

from common.osu.difficultycalculator import get_default_difficulty_calculator_class
from common.osu.enums import BeatmapStatus, Gamemode
from common.osu.utils import calculate_pp_total
from ppraces.enums import PPRaceStatus
from ppraces.models import PPRace, PPRacePlayer, PPRaceScore, PPRaceTeam
from profiles.enums import ScoreSet
from profiles.models import Score


@transaction.atomic
def create_pprace_lobby(
    name: str,
    gamemode: Gamemode,
    teams: dict[str, list[int]],
) -> PPRace:
    """
    Create a lobby for a pp race
    """
    diffcalc = get_default_difficulty_calculator_class(gamemode)
    pprace = PPRace.objects.create(
        name=name,
        gamemode=gamemode,
        status=PPRaceStatus.LOBBY,
        pp_decay_base=0.95,
        calculator_engine=diffcalc.engine(),
        primary_performance_value="total",
    )
    for team_name, player_ids in teams.items():
        team = PPRaceTeam.objects.create(
            pprace=pprace, name=team_name, total_pp=0, score_count=0
        )
        for player_id in player_ids:
            PPRacePlayer.objects.create(
                user_id=player_id, team=team, pp=0, pp_contribution=0, score_count=0
            )
    return pprace


@transaction.atomic
def update_pprace_status(pprace: PPRace) -> PPRace:
    """
    Update the status of a pp race
    """
    assert pprace.status not in [
        PPRaceStatus.LOBBY,
        PPRaceStatus.FINISHED,
    ], "PPRace should not be in lobby or finished status"
    assert pprace.start_time is not None, "PPRace must have a start time"
    assert pprace.end_time is not None, "PPRace must have an end time"

    now = datetime.now(tz=timezone.utc)
    if now < pprace.start_time:
        pprace.status = PPRaceStatus.WAITING_TO_START
    elif now < pprace.end_time:
        pprace.status = PPRaceStatus.IN_PROGRESS
    else:
        pprace.status = PPRaceStatus.FINALISING
        if pprace.all_players_finalised():
            pprace.status = PPRaceStatus.FINISHED
            for team in pprace.teams.all():
                update_pprace_team(team)

    pprace.save()
    return pprace


@transaction.atomic
def update_pprace_team(team: PPRaceTeam) -> PPRaceTeam:
    """
    Update the total pp and score count of a team, and player pp contribution
    """
    pprace_scores = PPRaceScore.objects.filter(team_id=team.id)
    scores = Score.objects.filter(
        id__in=pprace_scores.values_list("score_id", flat=True),
    ).get_score_set(team.pprace.gamemode)

    pp_values = scores.values_list("performance_total", "user_stats__user_id")

    pp_contributions = {}
    pp_weight = 1
    total_pp = 0
    for pp_value, user_id in pp_values:
        weighted_pp = pp_value * pp_weight
        total_pp += weighted_pp
        if user_id not in pp_contributions:
            pp_contributions[user_id] = 0
        pp_contributions[user_id] += weighted_pp
        pp_weight *= team.pprace.pp_decay_base

    team.total_pp = total_pp
    team.score_count = len(pp_values)
    team.save()

    for player in team.players.all():
        if player.user_id in pp_contributions:
            player.pp_contribution = pp_contributions[player.user_id]
        else:
            player.pp_contribution = 0
        player.save()

    return team


@transaction.atomic
def update_pprace_player(player: PPRacePlayer) -> PPRacePlayer:
    """
    Update a single pp race player
    """
    team = player.team
    pprace = team.pprace

    scores = Score.objects.filter(
        user_stats__user_id=player.user_id,
        gamemode=pprace.gamemode,
        date__gte=pprace.start_time,
        date__lte=pprace.end_time,
        beatmap__status__in=[BeatmapStatus.RANKED, BeatmapStatus.APPROVED],
    ).get_score_set(
        pprace.gamemode,
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

    player.last_update = datetime.now(tz=timezone.utc)
    player.save()

    return player
