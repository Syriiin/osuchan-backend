import itertools
from datetime import datetime, timedelta, timezone
from typing import Iterable

from django.db import transaction

from common.error_reporter import ErrorReporter
from common.osu import utils
from common.osu.difficultycalculator import (
    AbstractDifficultyCalculator,
    DifficultyCalculatorException,
)
from common.osu.difficultycalculator import Score as DifficultyCalculatorScore
from common.osu.difficultycalculator import (
    get_difficulty_calculators_for_gamemode,
)
from common.osu.enums import BeatmapStatus, BitMods, Gamemode, Mods
from common.osu.osuapi import OsuApi, ScoreData
from leaderboards.models import Leaderboard, Membership
from profiles.enums import ScoreMutation, ScoreResult
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
            # usernames should really be unique, but we don't have an up to date view of the users so there may be clashes
            return (
                UserStats.objects.select_related("user")
                .filter(user__username__iexact=username, gamemode=gamemode)
                .first()
            )
    except UserStats.DoesNotExist:
        return None


@transaction.atomic
def refresh_user_from_api(
    user_id=None,
    username=None,
    gamemode: Gamemode = Gamemode.STANDARD,
    cooldown_seconds: int = 300,
):
    """
    Fetch and add user with top 100 scores
    """
    # Check for invalid inputs
    if not user_id and not username:
        raise ValueError("Must pass either username or user_id")

    user_stats = fetch_user(user_id=user_id, username=username, gamemode=gamemode)

    if user_stats is not None and user_stats.last_updated > (
        datetime.utcnow().replace(tzinfo=timezone.utc)
        - timedelta(seconds=cooldown_seconds)
    ):
        # User was last updated less than 5 minutes ago, so just return it
        return user_stats, False

    osu_api = OsuApi()

    # Fetch user data from osu api
    if user_id:
        user_data = osu_api.get_user_by_id(user_id, gamemode)
    else:
        user_data = osu_api.get_user_by_name(username, gamemode)

    # Check for response
    if user_data is None:
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
            return None, False
        else:
            # User either doesnt exist, is restricted, or name changed
            try:
                osu_user = OsuUser.objects.select_for_update().get(
                    username__iexact=username
                )
                # Fetch from osu api with user id incase of name change
                user_data = osu_api.get_user_by_id(osu_user.id, gamemode)

                if user_data is None:
                    # Restricted
                    osu_user.disabled = True
                    osu_user.save()
                    return None, False
            except OsuUser.DoesNotExist:
                # Doesnt exist
                return None, False

    # try to fetch user stats by id in case of namechange
    if user_id is None and user_stats is None:
        user_stats = fetch_user(user_id=user_data.user_id, gamemode=gamemode)

    if user_stats is not None:
        osu_user = user_stats.user
    else:
        user_stats = UserStats()
        user_stats.gamemode = gamemode

        # Get or create OsuUser model
        try:
            osu_user = OsuUser.objects.select_for_update().get(id=user_data.user_id)
        except OsuUser.DoesNotExist:
            osu_user = OsuUser(id=user_data.user_id)

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
    osu_user.username = user_data.username
    osu_user.country = user_data.country
    osu_user.join_date = user_data.join_date
    osu_user.disabled = False

    # Save OsuUser model
    osu_user.save()

    # Set OsuUser relation id on UserStats
    user_stats.user_id = osu_user.id

    # Update UserStats fields
    user_stats.playcount = user_data.playcount
    user_stats.playtime = user_data.playtime
    user_stats.level = user_data.level
    user_stats.ranked_score = user_data.ranked_score
    user_stats.total_score = user_data.total_score
    user_stats.rank = user_data.rank
    user_stats.country_rank = user_data.country_rank
    user_stats.pp = user_data.pp
    user_stats.accuracy = user_data.accuracy
    user_stats.count_300 = user_data.count_300
    user_stats.count_100 = user_data.count_100
    user_stats.count_50 = user_data.count_50
    user_stats.count_rank_ss = user_data.count_rank_ss
    user_stats.count_rank_ssh = user_data.count_rank_ssh
    user_stats.count_rank_s = user_data.count_rank_s
    user_stats.count_rank_sh = user_data.count_rank_sh
    user_stats.count_rank_a = user_data.count_rank_a

    user_stats.save()

    # Fetch date of latest score
    latest_score_date = (
        user_stats.scores.order_by("-date").values_list("date", flat=True).first()
    )

    # Fetch user scores from osu api
    score_data_list = []
    score_data_list.extend(osu_api.get_user_best_scores(user_stats.user_id, gamemode))
    score_data_list.extend(
        score
        for score in osu_api.get_user_recent_scores(user_stats.user_id, gamemode)
        if score.rank != "F"
        and (latest_score_date is None or score.date > latest_score_date)
    )

    # Process and add scores
    created_scores = add_scores_from_data(user_stats, score_data_list)

    if len(created_scores) > 0:
        difficulty_calculators = get_difficulty_calculators_for_gamemode(gamemode)
        for difficulty_calculator in difficulty_calculators:
            with difficulty_calculator() as calc:
                update_performance_calculations(created_scores, calc)

        # Recalculate with new scores added
        user_stats.recalculate()
        user_stats.save()

    return user_stats, True


@transaction.atomic
def refresh_user_recent_from_api(
    user_id: int,
    gamemode: Gamemode = Gamemode.STANDARD,
    cooldown_seconds: int = 300,
):
    """
    Fetch and update user recent scores
    """
    user_stats = fetch_user(user_id=user_id, gamemode=gamemode)

    if user_stats is None:
        # User does not exist in the db, so return None
        return None, False

    if user_stats.last_updated > (
        datetime.utcnow().replace(tzinfo=timezone.utc)
        - timedelta(seconds=cooldown_seconds)
    ):
        # User was last updated less than 1 minutes ago, so just return it
        return user_stats, False

    osu_api = OsuApi()

    # Fetch date of latest score
    latest_score_date = (
        user_stats.scores.order_by("-date").values_list("date", flat=True).first()
    )

    # Fetch user scores from osu api
    score_data_list = [
        score
        for score in osu_api.get_user_recent_scores(user_stats.user_id, gamemode)
        if score.rank != "F"
        and (latest_score_date is None or score.date > latest_score_date)
    ]

    # Process and add scores
    created_scores = add_scores_from_data(user_stats, score_data_list)

    if len(created_scores) > 0:
        difficulty_calculators = get_difficulty_calculators_for_gamemode(gamemode)
        for difficulty_calculator in difficulty_calculators:
            with difficulty_calculator() as calc:
                update_performance_calculations(created_scores, calc)

        # Recalculate with new scores added
        user_stats.recalculate()
        user_stats.save()

    return user_stats, True


@transaction.atomic
def refresh_beatmaps_from_api(beatmap_ids: Iterable[int]):
    """
    Fetches and adds a list of beatmaps from the osu api
    """
    osu_api = OsuApi()
    beatmaps = []
    for beatmap_id in beatmap_ids:
        beatmap_data = osu_api.get_beatmap(beatmap_id)

        if beatmap_data is None:
            continue

        if beatmap_data.status not in [
            BeatmapStatus.APPROVED,
            BeatmapStatus.RANKED,
            BeatmapStatus.LOVED,
        ]:
            continue

        beatmap = Beatmap.from_data(beatmap_data)

        beatmaps.append(beatmap)

    Beatmap.objects.bulk_create(beatmaps, ignore_conflicts=True)

    beatmaps_by_gamemode = {}
    for beatmap in beatmaps:
        if beatmap.gamemode not in beatmaps_by_gamemode:
            beatmaps_by_gamemode[beatmap.gamemode] = []
        beatmaps_by_gamemode[beatmap.gamemode].append(beatmap)

    for gamemode, beatmaps in beatmaps_by_gamemode.items():
        for difficulty_calculator_class in get_difficulty_calculators_for_gamemode(
            gamemode
        ):
            with difficulty_calculator_class() as difficulty_calculator:
                update_difficulty_calculations(beatmaps, difficulty_calculator)

    return beatmaps


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

    full_score_data_list: list[ScoreData] = []
    for beatmap_id in beatmap_ids:
        # Fetch score data from osu api
        osu_api = OsuApi()
        score_data_list = osu_api.get_user_scores_for_beatmap(
            beatmap_id, user_id, gamemode
        )

        full_score_data_list += score_data_list

    # Process add scores
    created_scores = add_scores_from_data(user_stats, full_score_data_list)

    if len(created_scores) > 0:
        for difficulty_calculator_class in get_difficulty_calculators_for_gamemode(
            gamemode
        ):
            with difficulty_calculator_class() as difficulty_calculator:
                update_performance_calculations(created_scores, difficulty_calculator)

        # Recalculate with new scores added
        user_stats.recalculate()
        user_stats.save()

    return created_scores


# TODO: refactor this
def add_scores_from_data(user_stats: UserStats, score_data_list: list[ScoreData]):
    """
    Adds a list of scores to the passed user_stats from the passed score_data_list.
    (requires all dicts to have beatmap_id set along with usual score data)
    """
    # Remove potential duplicates from a top 100 play also being in the recent 50
    unique_score_data_list = []
    for score_data in score_data_list:
        if score_data not in unique_score_data_list:
            unique_score_data_list.append(score_data)

    # Remove scores which already exist in db
    score_dates = [score.date for score in unique_score_data_list]
    existing_score_dates = user_stats.scores.filter(date__in=score_dates).values_list(
        "date", flat=True
    )
    new_score_data_list: list[ScoreData] = []
    for score_data in unique_score_data_list:
        if score_data.date not in existing_score_dates:
            new_score_data_list.append(score_data)

    # Fetch beatmaps from database in bulk
    beatmap_ids = [score.beatmap_id for score in new_score_data_list]
    beatmaps = list(Beatmap.objects.filter(id__in=beatmap_ids))

    missing_beatmaps = set(beatmap_ids) - set(beatmap.id for beatmap in beatmaps)
    beatmaps.extend(refresh_beatmaps_from_api(missing_beatmaps))

    gamemode = Gamemode(user_stats.gamemode)

    scores_to_create = []
    for score_data in new_score_data_list:
        score = Score()

        score.mutation = ScoreMutation.NONE

        # Update Score fields
        score.score = score_data.score
        score.count_300 = score_data.count_300
        score.count_100 = score_data.count_100
        score.count_50 = score_data.count_50
        score.count_miss = score_data.count_miss
        score.count_geki = score_data.count_geki
        score.count_katu = score_data.count_katu
        score.statistics = score_data.statistics
        score.best_combo = score_data.best_combo
        score.perfect = score_data.perfect
        score.mods = score_data.mods
        score.mods_json = score_data.mods_json
        score.is_stable = score_data.is_stable
        score.rank = score_data.rank
        score.date = score_data.date

        if not utils.mods_are_ranked(score.mods_json, score.is_stable):
            continue

        # Update foreign keys
        beatmap_id = score_data.beatmap_id
        try:
            score.beatmap = next(
                beatmap for beatmap in beatmaps if beatmap.id == beatmap_id
            )
        except StopIteration:
            # Beatmap not ranked/loved or otherwise missing
            continue

        score.user_stats = user_stats

        # Update convenience fields
        score.gamemode = gamemode
        if Mods.CLASSIC in score.mods_json:
            score.accuracy = utils.get_classic_accuracy(
                score.statistics,
                gamemode=gamemode,
            )
        else:
            score.accuracy = utils.get_lazer_accuracy(
                score.statistics, score.beatmap.hitobject_counts, gamemode
            )

        score.bpm = utils.get_bpm(score.beatmap.bpm, score.mods_json)
        score.length = utils.get_length(score.beatmap.drain_time, score.mods_json)
        score.circle_size = utils.get_cs(
            score.beatmap.circle_size, score.mods_json, Gamemode(score.gamemode)
        )
        score.approach_rate = utils.get_ar(score.beatmap.approach_rate, score.mods_json)
        score.overall_difficulty = utils.get_od(
            score.beatmap.overall_difficulty, score.mods_json
        )

        # Process score
        score.process()

        scores_to_create.append(score)

    # Bulk add and update and scores
    created_scores = Score.objects.bulk_create(scores_to_create)

    if gamemode == Gamemode.STANDARD:
        nochoke_mutations_to_create = [
            score.get_nochoke_mutation()
            for score in created_scores
            if score.result & ScoreResult.CHOKE
        ]
        created_scores.extend(Score.objects.bulk_create(nochoke_mutations_to_create))

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
    for beatmap in beatmaps:
        calculations.append(
            DifficultyCalculation(
                beatmap_id=beatmap.id,
                mods=BitMods.NONE,
                calculator_engine=difficulty_calculator.engine(),
                calculator_version=difficulty_calculator.version(),
            )
        )

    DifficultyCalculation.objects.bulk_create(
        calculations,
        update_conflicts=True,
        update_fields=["calculator_version"],
        unique_fields=["beatmap_id", "mods", "calculator_engine"],
    )

    values = list(
        itertools.chain.from_iterable(
            calculate_difficulty_values(calculations, difficulty_calculator)
        )
    )

    DifficultyValue.objects.bulk_create(
        values,
        update_conflicts=True,
        update_fields=["value"],
        unique_fields=["calculation_id", "name"],
    )

    # Delete outdated values (non-existent in current calculator)
    DifficultyValue.objects.filter(
        calculation_id__in=[c.id for c in calculations]
    ).exclude(id__in=[v.id for v in values]).delete()


@transaction.atomic
def update_performance_calculations(
    scores: Iterable[Score], difficulty_calculator: AbstractDifficultyCalculator
):
    """
    Update performance (and difficulty) calculations for passed scores using passed difficulty calculator.
    Existing calculations will be updated.
    """
    # Create or update difficulty calculations
    unique_beatmaps = set((score.beatmap_id, score.mods) for score in scores)
    difficulty_calculations = []
    for beatmap_id, mods in unique_beatmaps:
        difficulty_calculations.append(
            DifficultyCalculation(
                beatmap_id=beatmap_id,
                mods=mods,
                calculator_engine=difficulty_calculator.engine(),
                calculator_version=difficulty_calculator.version(),
            )
        )

    DifficultyCalculation.objects.bulk_create(
        difficulty_calculations,
        update_conflicts=True,
        update_fields=["calculator_version"],
        unique_fields=["beatmap_id", "mods", "calculator_engine"],
    )

    # Do difficulty calculations
    difficulty_values = list(
        itertools.chain.from_iterable(
            calculate_difficulty_values(difficulty_calculations, difficulty_calculator)
        )
    )

    # Create or update difficulty values
    DifficultyValue.objects.bulk_create(
        difficulty_values,
        update_conflicts=True,
        update_fields=["value"],
        unique_fields=["calculation_id", "name"],
    )

    # Delete outdated values (non-existent in current calculator)
    DifficultyValue.objects.filter(
        calculation_id__in=[c.id for c in difficulty_calculations]
    ).exclude(id__in=[v.id for v in difficulty_values]).delete()

    # Create or update performance calculations
    performance_calculations = []
    for score in scores:
        difficulty_calculation = next(
            calculation
            for calculation in difficulty_calculations
            if calculation.beatmap_id == score.beatmap_id
            and calculation.mods == score.mods
        )
        performance_calculations.append(
            PerformanceCalculation(
                score=score,
                difficulty_calculation_id=difficulty_calculation.id,
                calculator_engine=difficulty_calculator.engine(),
                calculator_version=difficulty_calculator.version(),
            )
        )

    PerformanceCalculation.objects.bulk_create(
        performance_calculations,
        update_conflicts=True,
        update_fields=["calculator_version", "difficulty_calculation_id"],
        unique_fields=["score_id", "calculator_engine"],
    )

    # Do performance calculations
    performance_values = list(
        itertools.chain.from_iterable(
            calculate_performance_values(
                performance_calculations, difficulty_calculator
            )
        )
    )

    # Create or update performance values
    PerformanceValue.objects.bulk_create(
        performance_values,
        update_conflicts=True,
        update_fields=["value"],
        unique_fields=["calculation_id", "name"],
    )

    # Delete outdated values (non-existent in current calculator)
    PerformanceValue.objects.filter(
        calculation_id__in=[c.id for c in performance_calculations]
    ).exclude(id__in=[v.id for v in performance_values]).delete()


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
            mods=utils.get_json_mods(difficulty_calculation.mods, False),
        )
        for difficulty_calculation in difficulty_calculations
    ]

    results = []
    try:
        results.extend(difficulty_calculator.calculate_scores(calc_scores))
    except DifficultyCalculatorException as e:
        error_reporter = ErrorReporter()
        error_reporter.report_error(e)

        # Batch failed, so let's try one by one to get as many values as possible
        for calc_score in calc_scores:
            try:
                results.append(difficulty_calculator.calculate_scores([calc_score])[0])
            except DifficultyCalculatorException as e:
                error_reporter.report_error(e)
                results.append(None)

    values = [
        [
            DifficultyValue(
                calculation_id=difficulty_calculation.id,
                name=name,
                value=value,
            )
            for name, value in result.difficulty_values.items()
        ]
        for difficulty_calculation, result in zip(difficulty_calculations, results)
        if result is not None
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
            mods=utils.get_json_mods(
                performance_calculation.score.mods,
                performance_calculation.score.is_stable,
            ),
            statistics=performance_calculation.score.statistics,
            combo=performance_calculation.score.best_combo,
        )
        for performance_calculation in performance_calculations
    ]

    results = []
    try:
        results.extend(difficulty_calculator.calculate_scores(calc_scores))
    except DifficultyCalculatorException as e:
        error_reporter = ErrorReporter()
        error_reporter.report_error(e)

        # Batch failed, so let's try one by one to get as many values as possible
        for calc_score in calc_scores:
            try:
                results.append(difficulty_calculator.calculate_scores([calc_score])[0])
            except DifficultyCalculatorException as e:
                error_reporter.report_error(e)
                results.append(None)

    values = [
        [
            PerformanceValue(
                calculation_id=performance_calculation.id,
                name=name,
                value=value,
            )
            for name, value in result.performance_values.items()
        ]
        for performance_calculation, result in zip(performance_calculations, results)
        if result is not None
    ]

    return values
