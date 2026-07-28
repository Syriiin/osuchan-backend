from datetime import datetime, timedelta, timezone

from django.db import transaction
from django.db.models import Count, F, FilteredRelation, Q

from common.osu.difficultycalculator import get_default_difficulty_calculator_class
from common.osu.enums import BeatmapStatus, Gamemode
from minigames.enums import MinigameStatus
from minigames.games import GameScore, game_registry
from minigames.models import (
    Minigame,
    MinigamePlayer,
    MinigameScore,
    MinigameStats,
    MinigameTeam,
)
from profiles.enums import ScoreMutation
from profiles.models import OsuUser, Score


@transaction.atomic
def create_minigame(
    game_type: str,
    name: str,
    gamemode: Gamemode,
    host: OsuUser,
    settings_data: dict,
    teams: list[str] | None = None,
    is_free_for_all: bool = False,
) -> Minigame:
    """
    Create a new minigame lobby.
    """
    game = game_registry[game_type]
    config = game.get_settings(settings_data)

    minigame = Minigame.objects.create(
        game_type=game_type,
        name=name,
        gamemode=gamemode,
        is_free_for_all=is_free_for_all,
        status=MinigameStatus.LOBBY,
        config=config,
        initial_state={},
        state={},
        host=host,
    )

    if not is_free_for_all:
        assert teams is not None and len(teams) >= 2
        for team_name in teams:
            MinigameTeam.objects.create(
                minigame=minigame,
                name=team_name,
                points=0,
                score_count=0,
            )

    return minigame


@transaction.atomic
def join_minigame(minigame: Minigame, user: OsuUser) -> MinigamePlayer:
    """
    Add a player to a minigame.
    """
    assert minigame.status in (
        MinigameStatus.LOBBY,
        MinigameStatus.WAITING_TO_START,
    ), "Minigame must not have started"

    assert not MinigamePlayer.objects.filter(
        team__minigame=minigame, user=user
    ).exists(), "Player is already in this game"

    assert not MinigamePlayer.objects.filter(
        user=user,
        team__minigame__status__in=(
            MinigameStatus.LOBBY,
            MinigameStatus.WAITING_TO_START,
            MinigameStatus.IN_PROGRESS,
            MinigameStatus.FINALISING,
        ),
    ).exists(), "Player is already in an active minigame"

    if minigame.is_free_for_all:
        team = MinigameTeam.objects.create(
            minigame=minigame,
            name=user.username,
            points=0,
            score_count=0,
        )
    else:
        team = (
            minigame.teams.annotate(player_count=Count("players"))
            .order_by("player_count")
            .first()
        )

    return MinigamePlayer.objects.create(
        team=team,
        user=user,
        points=0,
        score_count=0,
    )


@transaction.atomic
def leave_minigame(minigame: Minigame, user: OsuUser) -> None:
    """
    Remove player from a minigame.
    """
    assert minigame.status in (
        MinigameStatus.LOBBY,
        MinigameStatus.WAITING_TO_START,
    ), "Minigame must not have started"

    if minigame.is_free_for_all:
        MinigameTeam.objects.filter(minigame=minigame, players__user=user).delete()
    else:
        MinigamePlayer.objects.filter(team__minigame=minigame, user=user).delete()

    if minigame.status == MinigameStatus.WAITING_TO_START:
        populated_teams = (
            minigame.teams.annotate(player_count=Count("players"))
            .filter(player_count__gt=0)
            .count()
        )
        if populated_teams < 2:
            minigame.status = MinigameStatus.LOBBY
            minigame.save(update_fields=["status"])


@transaction.atomic
def move_minigame_team(
    minigame: Minigame, user: OsuUser, target_team_id: int
) -> MinigamePlayer:
    """
    Move a minigame player to another team.
    """
    assert minigame.status in (
        MinigameStatus.LOBBY,
        MinigameStatus.WAITING_TO_START,
    ), "Minigame must not have started"
    assert not minigame.is_free_for_all, "Cannot move teams in free-for-all"

    target_team = MinigameTeam.objects.get(id=target_team_id, minigame=minigame)
    player = MinigamePlayer.objects.get(team__minigame=minigame, user=user)
    player.team = target_team
    player.save(update_fields=["team"])

    return player


@transaction.atomic
def update_minigame_settings(minigame: Minigame, settings_data: dict) -> Minigame:
    """
    Updates the settings for a minigame lobby.
    """
    assert minigame.status == MinigameStatus.LOBBY, "Minigame must be in lobby"

    game_plugin = game_registry[minigame.game_type]
    minigame.config = game_plugin.get_settings(settings_data)
    minigame.save(update_fields=["config"])

    return minigame


@transaction.atomic
def update_minigame_status(minigame: Minigame) -> Minigame:
    """
    Update the status of a minigame.
    """
    assert minigame.status not in [
        MinigameStatus.LOBBY,
        MinigameStatus.FINISHED,
    ], "Minigame should not be in lobby or finished status"
    assert minigame.start_time is not None, "Minigame must have a start time"
    assert minigame.end_time is not None, "Minigame must have an end time"

    now = datetime.now(tz=timezone.utc)
    if now < minigame.start_time:
        minigame.status = MinigameStatus.WAITING_TO_START
    elif now < minigame.end_time:
        minigame.status = MinigameStatus.IN_PROGRESS
    else:
        minigame.status = MinigameStatus.FINALISING

    minigame.save()
    return minigame


@transaction.atomic
def delete_minigame(minigame: Minigame) -> None:
    """
    Delete a minigame lobby.
    """
    assert minigame.status == MinigameStatus.LOBBY, "Game must be in lobby status"
    minigame.delete()


@transaction.atomic
def start_minigame(minigame: Minigame, countdown: int) -> Minigame:
    """
    Sets a minigame to start in countdown seconds.
    """
    assert minigame.status == MinigameStatus.LOBBY, "Game must be in lobby status"

    populated_teams = minigame.teams.annotate(player_count=Count("players")).filter(
        player_count__gt=0
    )
    assert populated_teams.count() >= 2, "Must have at least 2 populated teams"

    now = datetime.now(tz=timezone.utc)
    minigame.start_time = now + timedelta(seconds=countdown)
    minigame.end_time = minigame.start_time + timedelta(
        seconds=minigame.config["game_length"]
    )
    initial_state = game_registry[minigame.game_type].get_initial_state(
        config=minigame.config,
        players=minigame.get_players_info(),
        teams=minigame.get_teams_info(),
        start_time=minigame.start_time,
    )
    minigame.initial_state = initial_state
    minigame.state = initial_state
    minigame.status = MinigameStatus.WAITING_TO_START
    minigame.save()
    return minigame


@transaction.atomic
def update_minigame_player_scores(player: MinigamePlayer) -> MinigamePlayer:
    """
    Updates scores for a single minigame player.
    """
    player = MinigamePlayer.objects.select_for_update().get(id=player.id)
    team = player.team
    minigame = team.minigame

    scores = Score.objects.filter(
        user_stats__user_id=player.user_id,
        gamemode=minigame.gamemode,
        mutation=ScoreMutation.NONE,
        date__gte=minigame.start_time,
        date__lte=minigame.end_time,
        beatmap__status__in=[BeatmapStatus.RANKED, BeatmapStatus.APPROVED],
    )

    minigame_scores = [
        MinigameScore(
            score=score,
            player=player,
            team=team,
            minigame=minigame,
            points=0,
        )
        for score in scores
    ]

    # prevent deadlock; not too sure why this works, but it seems to
    minigame_scores.sort(key=lambda ms: ms.score_id)

    MinigameScore.objects.bulk_create(
        minigame_scores,
        update_conflicts=True,
        update_fields=["points"],
        unique_fields=["player_id", "score_id"],
    )

    outdated_minigame_scores = MinigameScore.objects.filter(player=player).exclude(
        score_id__in=[score.id for score in scores]
    )
    outdated_minigame_scores.delete()

    player.scores_last_updated = datetime.now(tz=timezone.utc)
    player.save(update_fields=["scores_last_updated"])

    return player


@transaction.atomic
def recompute_minigame(minigame: Minigame) -> bool:
    """
    Recompute minigame state from current scores.
    Returns True if the game plugin reports a win condition was reached.
    """
    engine = get_default_difficulty_calculator_class(minigame.gamemode).engine()

    minigame_scores = (
        MinigameScore.objects.filter(minigame=minigame)
        .annotate(
            performance_calculation=FilteredRelation(
                "score__performance_calculations",
                condition=Q(score__performance_calculations__calculator_engine=engine),
            ),
            difficulty_calculation=FilteredRelation(
                "score__beatmap__difficulty_calculations",
                condition=Q(
                    score__beatmap__difficulty_calculations__calculator_engine=engine,
                    score__beatmap__difficulty_calculations__mods=F("score__mods"),
                ),
            ),
        )
        .annotate(
            performance_value=FilteredRelation(
                "performance_calculation__performance_values",
                condition=Q(performance_calculation__performance_values__name="total"),
            ),
            difficulty_value=FilteredRelation(
                "difficulty_calculation__difficulty_values",
                condition=Q(difficulty_calculation__difficulty_values__name="total"),
            ),
        )
        .annotate(
            score_performance_total=F("performance_value__value"),
            score_difficulty_total=F("difficulty_value__value"),
        )
        .order_by("score__date")
    )

    score_values = minigame_scores.values(
        "id",
        "player_id",
        "team_id",
        "score_id",
        "points",
        "score__score",
        "score__count_300",
        "score__count_100",
        "score__count_50",
        "score__count_miss",
        "score__best_combo",
        "score__perfect",
        "score__mods_json",
        "score__accuracy",
        "score__rank",
        "score__date",
        "score__beatmap__id",
        "score__beatmap__creator_name",
        "score__beatmap__status",
        "score__beatmap__title",
        "score__beatmap__artist",
        "score__beatmap__difficulty_name",
        "score__beatmap__approval_date",
        "score__beatmap__hitobject_counts",
        "score__bpm",
        "score__length",
        "score__overall_difficulty",
        "score__approach_rate",
        "score_performance_total",
        "score_difficulty_total",
    )

    game_scores = [
        GameScore(
            id=score_value["id"],
            player_id=score_value["player_id"],
            team_id=score_value["team_id"],
            score_id=score_value["score_id"],
            points=score_value["points"],
            score_score=score_value["score__score"],
            score_count_300=score_value["score__count_300"],
            score_count_100=score_value["score__count_100"],
            score_count_50=score_value["score__count_50"],
            score_count_miss=score_value["score__count_miss"],
            score_best_combo=score_value["score__best_combo"],
            score_perfect=score_value["score__perfect"],
            score_mods_json=score_value["score__mods_json"],
            score_accuracy=score_value["score__accuracy"],
            score_rank=score_value["score__rank"],
            score_date=score_value["score__date"],
            beatmap_id=score_value["score__beatmap__id"],
            beatmap_creator_name=score_value["score__beatmap__creator_name"],
            beatmap_status=score_value["score__beatmap__status"],
            beatmap_title=score_value["score__beatmap__title"],
            beatmap_artist=score_value["score__beatmap__artist"],
            beatmap_difficulty_name=score_value["score__beatmap__difficulty_name"],
            beatmap_approval_date=score_value["score__beatmap__approval_date"],
            beatmap_hitobject_counts=score_value["score__beatmap__hitobject_counts"],
            score_bpm=score_value["score__bpm"],
            score_length=score_value["score__length"],
            score_overall_difficulty=score_value["score__overall_difficulty"],
            score_approach_rate=score_value["score__approach_rate"],
            score_performance_total=score_value["score_performance_total"],
            score_difficulty_total=score_value["score_difficulty_total"],
        )
        for score_value in score_values
    ]

    game = game_registry[minigame.game_type]
    result = game.process_scores(
        scores=game_scores,
        config=minigame.config,
        initial_state=minigame.initial_state,
        current_time=datetime.now(tz=timezone.utc),
    )

    minigame.state = result["state"]
    minigame.save(update_fields=["state"])

    players = {
        player.id: player
        for player in MinigamePlayer.objects.filter(team__minigame=minigame)
    }
    for player in players.values():
        player.points = 0
        player.score_count = 0
    for player_id, data in result.get("players", {}).items():
        player = players[player_id]
        player.points = data["points"]
        player.score_count = data["score_count"]
    MinigamePlayer.objects.bulk_update(players.values(), ["points", "score_count"])

    teams = {team.id: team for team in MinigameTeam.objects.filter(minigame=minigame)}
    for team in teams.values():
        team.points = 0
        team.score_count = 0
    for team_id, data in result.get("teams", {}).items():
        team = teams[team_id]
        team.points = data["points"]
        team.score_count = data["score_count"]
    MinigameTeam.objects.bulk_update(teams.values(), ["points", "score_count"])

    MinigameScore.objects.filter(minigame=minigame).update(points=0)
    score_data = result.get("scores", {})
    minigame_scores_to_update = [
        MinigameScore(id=gs.id, points=score_data[gs.id]["points"])
        for gs in game_scores
        if gs.id in score_data
    ]
    MinigameScore.objects.bulk_update(minigame_scores_to_update, ["points"])

    minigame.state_last_computed = datetime.now(tz=timezone.utc)
    minigame.save(update_fields=["state_last_computed"])

    return result.get("win_condition_reached", False)


@transaction.atomic
def finish_minigame(minigame: Minigame) -> Minigame:
    """
    Finalise a minigame and declare the winner.
    """
    players = MinigamePlayer.objects.filter(team__minigame=minigame)
    for player in players:
        update_minigame_player_scores(player)
    recompute_minigame(minigame)

    assert minigame.winning_team is None

    # possible to have more than a 2-way tie, but only the top 2 teams are needed to determine if a tie occured
    top_teams = list(minigame.teams.order_by("-points")[:2])

    assert len(top_teams) == 2, "Must have atleast two teams to decide a winner"

    if top_teams[0].points > top_teams[1].points:
        minigame.winning_team = top_teams[0]
        for player in minigame.winning_team.players.all():
            try:
                minigame_stats = MinigameStats.objects.get(user=player.user)
            except MinigameStats.DoesNotExist:
                minigame_stats = MinigameStats(user=player.user, wins=0)

            minigame_stats.wins += 1
            minigame_stats.save()

    minigame.status = MinigameStatus.FINISHED
    minigame.save(update_fields=["status", "winning_team"])

    return minigame
