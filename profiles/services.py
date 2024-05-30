import itertools
from datetime import datetime, timedelta, timezone
from typing import Iterable

from django.db import transaction

from common.error_reporter import ErrorReporter
from common.osu import utils
from common.osu.apiv1 import OsuApiV1
from common.osu.difficultycalculator import (
    AbstractDifficultyCalculator,
    DifficultyCalculator,
    DifficultyCalculatorException,
)
from common.osu.difficultycalculator import Score as DifficultyCalculatorScore
from common.osu.enums import BeatmapStatus, Gamemode, Mods
from leaderboards.models import Leaderboard, Membership
from leaderboards.tasks import update_memberships
from profiles.models import (
    Beatmap,
    DifficultyCalculation,
    DifficultyValue,
    OsuUser,
    PerformanceCalculation,
    PerformanceValue,
    Score,
    UserStats,
)


def fetch_user(user_id=None, username=None, gamemode=Gamemode.STANDARD):
    """
    Fetch user from database (if it exists in there)
    """
    if not user_id and not username:
        raise ValueError("Must pass either username or user_id")

    try:
        if user_id:
            return UserStats.objects.select_related("user").get(
                user_id=user_id, gamemode=gamemode
            )
        else:
            return UserStats.objects.select_related("user").get(
                user__username__iexact=username, gamemode=gamemode
            )
    except UserStats.DoesNotExist:
        return None


@transaction.atomic
def refresh_user_from_api(
    user_id=None, username=None, gamemode: Gamemode = Gamemode.STANDARD
):
    """
    Fetch and add user with top 100 scores
    """
    # Check for invalid inputs
    if not user_id and not username:
        raise ValueError("Must pass either username or user_id")

    user_stats = fetch_user(user_id=user_id, username=username, gamemode=gamemode)

    if user_stats is not None and user_stats.last_updated > (
        datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(minutes=5)
    ):
        # User was last updated less than 5 minutes ago, so just return it
        return user_stats

    osu_api_v1 = OsuApiV1()

    # Fetch user data from osu api
    if user_id:
        user_data = osu_api_v1.get_user_by_id(user_id, gamemode)
    else:
        user_data = osu_api_v1.get_user_by_name(username, gamemode)

    # Check for response
    if not user_data:
        if user_id:
            # User either doesnt exist, or is restricted and needs to be disabled
            try:
                osu_user = OsuUser.objects.select_for_update().get(id=user_id)
                # Restricted
                osu_user.disabled = True
                osu_user.save()
            except OsuUser.DoesNotExist:
                # Doesnt exist (or was restricted before osuchan ever saw them)
                pass
            return None
        else:
            # User either doesnt exist, is restricted, or name changed
            try:
                osu_user = OsuUser.objects.select_for_update().get(username=username)
                # Fetch from osu api with user id incase of name change
                user_data = osu_api_v1.get_user_by_id(osu_user.id, gamemode)

                if not user_data:
                    # Restricted
                    osu_user.disabled = True
                    osu_user.save()
                    return None
            except OsuUser.DoesNotExist:
                # Doesnt exist
                return None

    if user_stats is not None:
        osu_user = user_stats.user
    else:
        user_stats = UserStats()
        user_stats.gamemode = gamemode

        # Get or create OsuUser model
        try:
            osu_user = OsuUser.objects.select_for_update().get(id=user_data["user_id"])
        except OsuUser.DoesNotExist:
            osu_user = OsuUser(id=user_data["user_id"])

            # Create memberships with global leaderboards
            global_leaderboards = Leaderboard.global_leaderboards.values("id")
            # TODO: refactor this to be somewhere else. dont really like setting values to 0
            global_memberships = [
                Membership(
                    leaderboard_id=leaderboard["id"],
                    user_id=osu_user.id,
                    pp=0,
                    rank=0,
                    score_count=0,
                )
                for leaderboard in global_leaderboards
            ]
            Membership.objects.bulk_create(global_memberships)

    # Update OsuUser fields
    osu_user.username = user_data["username"]
    osu_user.country = user_data["country"]
    osu_user.join_date = datetime.strptime(
        user_data["join_date"], "%Y-%m-%d %H:%M:%S"
    ).replace(tzinfo=timezone.utc)
    osu_user.disabled = False

    # Save OsuUser model
    osu_user.save()

    # Set OsuUser relation id on UserStats
    user_stats.user_id = int(osu_user.id)

    # Update UserStats fields
    user_stats.playcount = (
        int(user_data["playcount"]) if user_data["playcount"] is not None else 0
    )
    user_stats.playtime = (
        int(user_data["total_seconds_played"])
        if user_data["total_seconds_played"] is not None
        else 0
    )
    user_stats.level = (
        float(user_data["level"]) if user_data["level"] is not None else 0
    )
    user_stats.ranked_score = (
        int(user_data["ranked_score"]) if user_data["ranked_score"] is not None else 0
    )
    user_stats.total_score = (
        int(user_data["total_score"]) if user_data["total_score"] is not None else 0
    )
    user_stats.rank = (
        int(user_data["pp_rank"]) if user_data["pp_rank"] is not None else 0
    )
    user_stats.country_rank = (
        int(user_data["pp_country_rank"])
        if user_data["pp_country_rank"] is not None
        else 0
    )
    user_stats.pp = float(user_data["pp_raw"]) if user_data["pp_raw"] is not None else 0
    user_stats.accuracy = (
        float(user_data["accuracy"]) if user_data["accuracy"] is not None else 0
    )
    user_stats.count_300 = (
        int(user_data["count300"]) if user_data["count300"] is not None else 0
    )
    user_stats.count_100 = (
        int(user_data["count100"]) if user_data["count100"] is not None else 0
    )
    user_stats.count_50 = (
        int(user_data["count50"]) if user_data["count50"] is not None else 0
    )
    user_stats.count_rank_ss = (
        int(user_data["count_rank_ss"]) if user_data["count_rank_ss"] is not None else 0
    )
    user_stats.count_rank_ssh = (
        int(user_data["count_rank_ssh"])
        if user_data["count_rank_ssh"] is not None
        else 0
    )
    user_stats.count_rank_s = (
        int(user_data["count_rank_s"]) if user_data["count_rank_s"] is not None else 0
    )
    user_stats.count_rank_sh = (
        int(user_data["count_rank_sh"]) if user_data["count_rank_sh"] is not None else 0
    )
    user_stats.count_rank_a = (
        int(user_data["count_rank_a"]) if user_data["count_rank_a"] is not None else 0
    )

    # Fetch user scores from osu api
    score_data_list = []
    score_data_list.extend(
        osu_api_v1.get_user_best_scores(user_stats.user_id, gamemode)
    )
    if gamemode == Gamemode.STANDARD:
        # If standard, check user recent because we will be able to calculate pp for those scores
        score_data_list.extend(
            score
            for score in osu_api_v1.get_user_recent_scores(user_stats.user_id, gamemode)
            if score["rank"] != "F"
        )

    user_stats.save()

    # Process and add scores
    created_scores = add_scores_from_data(user_stats, score_data_list)

    # TODO: iterate all registered difficulty calculators for gamemode
    if gamemode == Gamemode.STANDARD:
        difficulty_calculator = DifficultyCalculator()
        for score in created_scores:
            update_performance_calculation(score, difficulty_calculator)

    return user_stats


@transaction.atomic
def refresh_beatmap_from_api(beatmap_id: int):
    """
    Fetch and add a beatmap
    """
    osu_api_v1 = OsuApiV1()
    beatmap_data = osu_api_v1.get_beatmap(beatmap_id)

    if beatmap_data is None:
        return None

    beatmap = Beatmap.from_data(beatmap_data)
    if beatmap.status not in [
        BeatmapStatus.APPROVED,
        BeatmapStatus.RANKED,
        BeatmapStatus.LOVED,
    ]:
        return None

    beatmap.save()

    return beatmap


@transaction.atomic
def fetch_scores(user_id, beatmap_ids, gamemode):
    """
    Fetch and add scores for a user on beatmaps in a gamemode
    """
    # Fetch UserStats from database
    try:
        user_stats = UserStats.objects.select_for_update().get(
            user_id=user_id, gamemode=gamemode
        )
    except UserStats.DoesNotExist:
        return []

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
    created_scores = add_scores_from_data(user_stats, full_score_data_list)

    # TODO: iterate all registered difficulty calculators for gamemode
    difficulty_calculator = DifficultyCalculator()
    for score in created_scores:
        update_performance_calculation(score, difficulty_calculator)

    return created_scores


# TODO: refactor this
def add_scores_from_data(user_stats: UserStats, score_data_list: list[dict]):
    """
    Adds a list of scores to the passed user_stats from the passed score_data_list.
    (requires all dicts to have beatmap_id set along with usual score data)
    """
    # Remove unranked scores
    # Only process "high scores" (highest scorev1 per mod per map per user)
    # (need to make this distinction to prevent lazer scores from being treated as ranked)
    ranked_score_data_list = [
        score_data
        for score_data in score_data_list
        if score_data.get("score_id", None) is not None
    ]

    # Parse dates
    for score_data in ranked_score_data_list:
        score_data["date"] = datetime.strptime(
            score_data["date"], "%Y-%m-%d %H:%M:%S"
        ).replace(tzinfo=timezone.utc)

    # Remove potential duplicates from a top 100 play also being in the recent 50
    # Unique on date since we don't track score_id (not ideal but not much we can do)
    unique_score_data_list = [
        score
        for score in ranked_score_data_list
        if score
        == next(s for s in ranked_score_data_list if s["date"] == score["date"])
    ]

    # Remove scores which already exist in db
    score_dates = [s["date"] for s in unique_score_data_list]
    existing_score_dates = Score.objects.filter(date__in=score_dates).values_list(
        "date", flat=True
    )
    new_score_data_list = []
    for score_data in unique_score_data_list:
        if score_data["date"] not in existing_score_dates:
            new_score_data_list.append(score_data)

    # Fetch beatmaps from database in bulk
    beatmap_ids = [int(s["beatmap_id"]) for s in new_score_data_list]
    beatmaps = list(Beatmap.objects.filter(id__in=beatmap_ids))

    scores_to_create = []
    for score_data in new_score_data_list:
        score = Score()

        # Update Score fields
        score.score = int(score_data["score"])
        score.count_300 = int(score_data["count300"])
        score.count_100 = int(score_data["count100"])
        score.count_50 = int(score_data["count50"])
        score.count_miss = int(score_data["countmiss"])
        score.count_geki = int(score_data["countgeki"])
        score.count_katu = int(score_data["countkatu"])
        score.best_combo = int(score_data["maxcombo"])
        score.perfect = bool(int(score_data["perfect"]))
        score.mods = int(score_data["enabled_mods"])
        score.rank = score_data["rank"]
        score.date = score_data["date"]

        if score.mods & Mods.UNRANKED != 0:
            continue

        # Update foreign keys
        # Search for beatmap in fetched, else create it
        beatmap_id = int(score_data["beatmap_id"])
        beatmap = next(
            (beatmap for beatmap in beatmaps if beatmap.id == beatmap_id), None
        )
        if beatmap is None:
            beatmap = refresh_beatmap_from_api(beatmap_id)
            if beatmap is None:
                continue

            # add to beatmaps incase another score is on this map
            beatmaps.append(beatmap)
        score.beatmap = beatmap
        score.user_stats = user_stats

        # Update pp
        if "pp" in score_data and score_data["pp"] is not None:
            score.performance_total = float(score_data["pp"])
            score.difficulty_calculator_engine = "legacy"
            score.difficulty_calculator_version = "legacy"
        else:
            # Check for gamemode
            if user_stats.gamemode != Gamemode.STANDARD:
                # We cant calculate pp for this mode yet so we need to disregard this score
                continue

            try:
                with DifficultyCalculator() as calc:
                    calculation = calc.calculate_score(
                        DifficultyCalculatorScore(
                            mods=score.mods,
                            beatmap_id=beatmap_id,
                            count_100=score.count_100,
                            count_50=score.count_50,
                            count_miss=score.count_miss,
                            combo=score.best_combo,
                        )
                    )
                    score.performance_total = calculation.performance_values["total"]
                    score.difficulty_calculator_engine = DifficultyCalculator.engine()
                    score.difficulty_calculator_version = DifficultyCalculator.version()
            except DifficultyCalculatorException as e:
                error_reporter = ErrorReporter()
                error_reporter.report_error(e)
                continue

        # Update convenience fields
        score.gamemode = user_stats.gamemode
        score.accuracy = utils.get_accuracy(
            score.count_300,
            score.count_100,
            score.count_50,
            score.count_miss,
            score.count_katu,
            score.count_geki,
            gamemode=user_stats.gamemode,
        )
        score.bpm = utils.get_bpm(beatmap.bpm, score.mods)
        score.length = utils.get_length(beatmap.drain_time, score.mods)
        score.circle_size = utils.get_cs(
            beatmap.circle_size, score.mods, score.gamemode
        )
        score.approach_rate = utils.get_ar(beatmap.approach_rate, score.mods)
        score.overall_difficulty = utils.get_od(beatmap.overall_difficulty, score.mods)

        # Process score
        score.process()

        scores_to_create.append(score)

    # Bulk add and update and scores
    created_scores = Score.objects.bulk_create(scores_to_create)

    # Recalculate with new scores added
    user_stats.recalculate()
    user_stats.save()

    # Return new scores
    return created_scores


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
    All scores must be for the passed beatmap_id and mods.
    Existing calculations will be updated.
    """
    # Validate all scores are of same beatmap/mods
    for score in scores:
        if score.beatmap_id != beatmap_id or score.mods != mods:
            raise ValueError(
                f"Score {score.id} does not match beatmap {beatmap_id} and mods {mods}"
            )

    # Create or update difficulty calculation
    difficulty_calculation, _ = DifficultyCalculation.objects.update_or_create(
        beatmap_id=beatmap_id,
        mods=mods,
        calculator_engine=difficulty_calculator.engine(),
        defaults={"calculator_version": difficulty_calculator.version()},
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


@transaction.atomic
def update_performance_calculation(
    score: Score, difficulty_calculator: AbstractDifficultyCalculator
):
    """
    Update performance (and difficulty) calculations for passed score using passed difficulty calculator.
    """
    # Create difficulty calculation
    difficulty_calculation, _ = DifficultyCalculation.objects.update_or_create(
        beatmap_id=score.beatmap_id,
        mods=score.mods,
        calculator_engine=difficulty_calculator.engine(),
        defaults={"calculator_version": difficulty_calculator.version()},
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

    # Create performance calculation
    performance_calculation, _ = PerformanceCalculation.objects.update_or_create(
        score=score,
        difficulty_calculation_id=difficulty_calculation.id,
        calculator_engine=difficulty_calculator.engine(),
        defaults={"calculator_version": difficulty_calculator.version()},
    )

    performance_values = calculate_performance_values(
        [performance_calculation], difficulty_calculator
    )[0]

    PerformanceValue.objects.bulk_create(
        performance_values,
        update_conflicts=True,
        update_fields=["value"],
        unique_fields=["calculation_id", "name"],
    )


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

    values = [
        [
            DifficultyValue(
                calculation_id=difficulty_calculation.id,
                name=name,
                value=value,
            )
        ]
        for difficulty_calculation, result in zip(difficulty_calculations, results)
        for name, value in result.difficulty_values.items()
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
                name=name,
                value=value,
            )
        ]
        for performance_calculation, result in zip(performance_calculations, results)
        for name, value in result.performance_values.items()
    ]

    return values
