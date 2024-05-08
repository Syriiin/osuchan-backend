import itertools
from datetime import datetime, timedelta, timezone
from typing import Iterable

from django.db import transaction

from common.error_reporter import ErrorReporter
from common.osu.apiv1 import OsuApiV1
from common.osu.difficultycalculator import (
    AbstractDifficultyCalculator,
    DifficultyCalculatorException,
)
from common.osu.difficultycalculator import Score as DifficultyCalculatorScore
from common.osu.enums import Gamemode, Mods
from profiles.models import (
    Beatmap,
    DifficultyCalculation,
    DifficultyValue,
    PerformanceCalculation,
    PerformanceValue,
    Score,
    UserStats,
)
from profiles.tasks import update_user


def fetch_user(user_id=None, username=None, gamemode=Gamemode.STANDARD):
    """
    Fetch user from database and enqueue update (max once each 5 minutes)
    """
    # Check for invalid inputs
    if not user_id and not username:
        raise ValueError("Must pass either username or user_id")

    # Attempt to get the UserStats model and enqueue update
    try:
        if user_id:
            user_stats = UserStats.objects.select_related("user").get(
                user_id=user_id, gamemode=gamemode
            )
        else:
            user_stats = UserStats.objects.select_related("user").get(
                user__username__iexact=username, gamemode=gamemode
            )

        if user_stats.last_updated < (
            datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(minutes=5)
        ):
            # User was last updated more than 5 minutes ago, so enqueue another update
            update_user.delay(user_id=user_stats.user_id, gamemode=gamemode)
    except UserStats.DoesNotExist:
        # User not in database, either doesn't exist or is first time seeing this user (or namechange)
        # Calling update_user in a blocking way here because otherwise we would be showing the user to not exist, before we know that for sure
        # TODO: maybe get rid of this in favor of some sort of realtime update progress display to the user via websockets observing celery events
        user_stats = update_user(user_id=user_id, username=username, gamemode=gamemode)

    return user_stats


@transaction.atomic
def fetch_scores(user_id, beatmap_ids, gamemode):
    """
    Fetch and add scores for a user on beatmaps in a gamemode
    """
    # Fetch UserStats from database
    user_stats = UserStats.objects.select_for_update().get(
        user_id=user_id, gamemode=gamemode
    )

    full_score_data_list = []
    for beatmap_id in beatmap_ids:
        # Fetch score data from osu api
        osu_api_v1 = OsuApiV1()
        score_data_list = osu_api_v1.get_user_scores_for_beatmap(
            beatmap_id, user_id, gamemode
        )

        # Add beatmap id to turn it into the common json format
        for score_data in score_data_list:
            score_data["beatmap_id"] = beatmap_id

        full_score_data_list += score_data_list

    # Process add scores
    new_scores = user_stats.add_scores_from_data(full_score_data_list)

    return new_scores


@transaction.atomic
def update_difficulty_calculations(
    beatmaps: Iterable[Beatmap], difficulty_calculator: AbstractDifficultyCalculator
):
    """
    Update difficulty calculations for passed beatmaps using passed difficulty calculator.
    Existing calculations will be updated.
    """
    # Create calculations
    calculations = []
    beatmap_ids = []
    for beatmap in beatmaps:
        calculations.append(
            DifficultyCalculation(
                beatmap_id=beatmap.id,
                mods=Mods.NONE,
                calculator_engine=difficulty_calculator.engine(),
                calculator_version=difficulty_calculator.version(),
            )
        )
        beatmap_ids.append(beatmap.id)

    DifficultyCalculation.objects.bulk_create(
        calculations,
        update_conflicts=True,
        update_fields=["calculator_version"],
        unique_fields=["beatmap_id", "mods", "calculator_engine"],
    )
    # TODO: remove when bulk_create(update_conflicts) returns pks in django 5.0
    calculations = DifficultyCalculation.objects.filter(
        beatmap_id__in=beatmap_ids,
        mods=Mods.NONE,
        calculator_engine=difficulty_calculator.engine(),
    )

    values = calculate_difficulty_values(calculations, difficulty_calculator)

    DifficultyValue.objects.bulk_create(
        itertools.chain.from_iterable(values),
        update_conflicts=True,
        update_fields=["value"],
        unique_fields=["calculation_id", "name"],
    )

    # TODO: what happens if the calculator is updated to remove a diff value?
    #   do we need to delete all values not returned for a calculation?
    #   with update_conflicts=True returning pks in django 5.0 we can just add a delete where not id in pks


@transaction.atomic
def update_performance_calculations_for_unique_beatmap(
    beatmap_id: int,
    mods: Mods,
    scores: Iterable[Score],
    difficulty_calculator: AbstractDifficultyCalculator,
):
    """
    Update performance (and difficulty) calculations for passed scores using passed difficulty calculator.
    Existing calculations will be updated.
    """
    # Validate all scores are of same beatmap/mods
    for score in scores:
        if score.beatmap_id != beatmap_id or score.mods != mods:
            raise ValueError(
                f"Score {score.id} does not match beatmap {beatmap_id} and mods {mods}"
            )

    # Create difficulty calculation
    difficulty_calculation, _ = DifficultyCalculation.objects.get_or_create(
        beatmap_id=beatmap_id,
        mods=mods,
        calculator_engine=difficulty_calculator.engine(),
        calculator_version=difficulty_calculator.version(),
    )

    # Do difficulty calculation
    difficulty_values = calculate_difficulty_values(
        [difficulty_calculation], difficulty_calculator
    )[0]
    DifficultyValue.objects.bulk_create(
        difficulty_values,
        update_conflicts=True,
        update_fields=["value"],
        unique_fields=["calculation_id", "name"],
    )

    # TODO: delete potentially outdated (removed from calc) values?

    # Create calculations
    score_ids = []
    performance_calculations = []
    for score in scores:
        performance_calculations.append(
            PerformanceCalculation(
                score=score,
                difficulty_calculation_id=difficulty_calculation.id,
                calculator_engine=difficulty_calculator.engine(),
                calculator_version=difficulty_calculator.version(),
            )
        )
        score_ids.append(score.id)

    PerformanceCalculation.objects.bulk_create(
        performance_calculations,
        update_conflicts=True,
        update_fields=["calculator_version", "difficulty_calculation_id"],
        unique_fields=["score_id", "calculator_engine"],
    )
    # TODO: remove when bulk_create(update_conflicts) returns pks in django 5.0
    performance_calculations = PerformanceCalculation.objects.filter(
        score_id__in=score_ids,
        calculator_engine=difficulty_calculator.engine(),
    )

    values = calculate_performance_values(
        performance_calculations, difficulty_calculator
    )

    PerformanceValue.objects.bulk_create(
        itertools.chain.from_iterable(values),
        update_conflicts=True,
        update_fields=["value"],
        unique_fields=["calculation_id", "name"],
    )

    # TODO: what happens if the calculator is updated to remove a perf value?
    #   do we need to delete all values not returned for a calculation?
    #   with update_conflicts=True returning pks in django 5.0 we can just add a delete where not id in pks


def calculate_difficulty_values(
    difficulty_calculations: Iterable[DifficultyCalculation],
    difficulty_calculator: AbstractDifficultyCalculator,
) -> list[list[DifficultyValue]]:
    """
    Calculate difficulty values for the passed difficulty calculations using passed difficulty calculator.
    """
    calc_scores = [
        DifficultyCalculatorScore(
            beatmap_id=str(difficulty_calculation.beatmap_id),
            mods=difficulty_calculation.mods,
        )
        for difficulty_calculation in difficulty_calculations
    ]

    results = difficulty_calculator.calculate_score_batch(calc_scores)

    # TODO: handle multiple values per calculation
    #   do we need a "primary" or "total" boolean to determine the main value?
    #   or should calculation have a "primary_value" field?
    #   or should we just always use "total" as the main value?
    values = [
        [
            DifficultyValue(
                calculation_id=difficulty_calculation.id,
                name="total",
                value=result.difficulty,
            )
        ]
        for difficulty_calculation, result in zip(difficulty_calculations, results)
    ]

    return values


def calculate_performance_values(
    performance_calculations: Iterable[PerformanceCalculation],
    difficulty_calculator: AbstractDifficultyCalculator,
) -> list[list[PerformanceValue]]:
    """
    Calculate performance values for the passed performance calculations using passed difficulty calculator.
    """
    calc_scores = [
        DifficultyCalculatorScore(
            beatmap_id=str(performance_calculation.score.beatmap_id),
            mods=performance_calculation.score.mods,
            count_100=performance_calculation.score.count_100,
            count_50=performance_calculation.score.count_50,
            count_miss=performance_calculation.score.count_miss,
            combo=performance_calculation.score.best_combo,
        )
        for performance_calculation in performance_calculations
    ]

    results = difficulty_calculator.calculate_score_batch(calc_scores)

    values = [
        [
            PerformanceValue(
                calculation_id=performance_calculation.id,
                name="total",
                value=result.performance,
            )
        ]
        for performance_calculation, result in zip(performance_calculations, results)
    ]

    return values
