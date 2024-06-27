from typing import Iterable, Type

from django.core.management.base import BaseCommand
from django.core.paginator import Paginator
from django.db.models import FilteredRelation, Q, QuerySet
from tqdm import tqdm

from common.error_reporter import ErrorReporter
from common.osu.difficultycalculator import (
    AbstractDifficultyCalculator,
    CalculationException,
    get_difficulty_calculator_class,
    get_difficulty_calculators_for_gamemode,
)
from common.osu.enums import Gamemode
from leaderboards.models import Membership
from leaderboards.services import update_membership
from profiles.models import Beatmap, Score, UserStats
from profiles.services import (
    update_difficulty_calculations,
    update_performance_calculations,
)


class Command(BaseCommand):
    help = "Recalculates beatmap difficulty values, score performance values and user stats score styles"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force recalculation of beatmaps and scores even if already up to date",
        )
        parser.add_argument(
            "--diffcalc",
            help="Name of calculator to use, leaving blank will use the default",
        )

    def handle(self, *args, **options):
        force = options["force"]
        diffcalc_name = options["diffcalc"]

        if diffcalc_name:
            difficulty_calculator_class = get_difficulty_calculator_class(diffcalc_name)
        else:
            difficulty_calculator_class = get_difficulty_calculators_for_gamemode(
                Gamemode.STANDARD
            )[0]

        with difficulty_calculator_class() as difficulty_calculator:

            gamemode = difficulty_calculator.gamemode()
            self.stdout.write(
                f"Gamemode: {Gamemode(gamemode).name}\n"
                f"Difficulty Calculator Engine: {difficulty_calculator.engine()}\n"
                f"Difficulty Calculator Version: {difficulty_calculator.version()}\n"
            )

            # Recalculate beatmaps
            beatmaps = Beatmap.objects.filter(gamemode=gamemode)
            self.recalculate_beatmaps(difficulty_calculator, beatmaps, force)

            # Recalculate scores
            scores = Score.objects.filter(gamemode=gamemode)
            self.recalculate_scores(difficulty_calculator, scores, force)

            # Recalculate user stats
            all_user_stats = UserStats.objects.filter(gamemode=gamemode)
            self.recalculate_user_stats(all_user_stats)

            # Recalculate memberships
            memberships = Membership.objects.select_related("leaderboard").filter(
                leaderboard__gamemode=gamemode
            )
            self.recalculate_memberships(memberships)

    def recalculate_beatmaps(
        self,
        difficulty_calculator: AbstractDifficultyCalculator,
        beatmaps: QuerySet[Beatmap],
        force: bool = False,
    ):
        if force:
            self.stdout.write(f"Forcing recalculation of all beatmaps...")

            paginator = Paginator(beatmaps.order_by("pk"), per_page=2000)

            with tqdm(desc="Beatmaps", total=beatmaps.count(), smoothing=0) as pbar:
                for page in paginator:
                    try:
                        update_difficulty_calculations(page, difficulty_calculator)
                    except CalculationException as e:
                        ErrorReporter().report_error(e)
                        pbar.write(
                            self.style.ERROR(
                                f"Error calculating difficulty values for beatmaps: {e}"
                            )
                        )

                    pbar.update(len(page))
        else:
            beatmaps_to_recalculate = beatmaps.annotate(
                difficulty_calculation=FilteredRelation(
                    "difficulty_calculations",
                    condition=Q(
                        difficulty_calculations__mods=0,
                        difficulty_calculations__calculator_engine=difficulty_calculator.engine(),
                        difficulty_calculations__calculator_version=difficulty_calculator.version(),
                    ),
                )
            ).filter(difficulty_calculation=None)

            if beatmaps_to_recalculate.count() == 0:
                self.stdout.write(f"All {beatmaps.count()} beatmaps already up to date")
                return

            count_up_to_date = beatmaps.count() - beatmaps_to_recalculate.count()

            if count_up_to_date > 0:
                self.stdout.write(
                    f"Found {count_up_to_date} beatmaps already up to date. Resuming..."
                )

            with tqdm(
                desc="Beatmaps",
                total=beatmaps.count(),
                initial=count_up_to_date,
                smoothing=0,
            ) as pbar:
                while len(page := beatmaps_to_recalculate[:2000]) > 0:
                    try:
                        update_difficulty_calculations(page, difficulty_calculator)
                    except CalculationException as e:
                        ErrorReporter().report_error(e)
                        pbar.write(
                            self.style.ERROR(
                                f"Error calculating difficulty values for beatmaps: {e}\n"
                                f"Skipping {len(page)} beatmaps in batch"
                            )
                        )
                        beatmaps_to_recalculate = beatmaps_to_recalculate.exclude(
                            pk__in=[beatmap.pk for beatmap in page]
                        )

                    pbar.update(len(page))

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully updated {beatmaps.count()} beatmaps' difficulty values"
            )
        )

    def recalculate_scores(
        self,
        difficulty_calculator: AbstractDifficultyCalculator,
        scores: QuerySet[Score],
        force: bool = False,
    ):
        if force:
            self.stdout.write(f"Forcing recalculation of all scores...")

            paginator = Paginator(scores.order_by("beatmap_id", "mods"), per_page=2000)

            with tqdm(desc="Scores", total=scores.count(), smoothing=0) as pbar:
                for page in paginator:
                    try:
                        update_performance_calculations(page, difficulty_calculator)
                    except CalculationException as e:
                        ErrorReporter().report_error(e)
                        pbar.write(
                            self.style.ERROR(
                                f"Error calculating performance values: {e}"
                            )
                        )

                    pbar.update(len(page))
        else:
            scores_to_recalculate = scores.annotate(
                performance_calculation=FilteredRelation(
                    "performance_calculations",
                    condition=Q(
                        performance_calculations__calculator_engine=difficulty_calculator.engine(),
                        performance_calculations__calculator_version=difficulty_calculator.version(),
                    ),
                )
            ).filter(performance_calculation=None)

            if scores_to_recalculate.count() == 0:
                self.stdout.write(f"All {scores.count()} scores already up to date")
                return

            count_up_to_date = scores.count() - scores_to_recalculate.count()

            if count_up_to_date > 0:
                self.stdout.write(
                    f"Found {count_up_to_date} scores already up to date. Resuming..."
                )

            # order by beatmap_id and mods to group scores by unique beatmaps for efficiency
            scores_to_recalculate = scores_to_recalculate.order_by("beatmap_id", "mods")

            with tqdm(
                desc="Scores",
                total=scores.count(),
                initial=count_up_to_date,
                smoothing=0,
            ) as pbar:
                while len(page := scores_to_recalculate[:2000]) > 0:
                    try:
                        update_performance_calculations(
                            page,
                            difficulty_calculator,
                        )
                    except CalculationException as e:
                        ErrorReporter().report_error(e)
                        pbar.write(
                            self.style.ERROR(
                                f"Error calculating performance values: {e}\n"
                                f"Skipping {len(page)} scores in batch"
                            )
                        )
                        scores_to_recalculate = scores_to_recalculate.exclude(
                            pk__in=[score.pk for score in page]
                        )

                    pbar.update(len(page))

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully updated {scores.count()} scores' performance values"
            )
        )

    def recalculate_user_stats(
        self,
        all_user_stats: QuerySet[UserStats],
    ):
        paginator = Paginator(all_user_stats.order_by("pk"), per_page=2000)

        with tqdm(desc="User Stats", total=all_user_stats.count(), smoothing=0) as pbar:
            for page in paginator:
                for user_stats in page:
                    user_stats.recalculate()
                    pbar.update()
                UserStats.objects.bulk_update(
                    page,
                    [
                        "extra_pp",
                        "score_style_accuracy",
                        "score_style_bpm",
                        "score_style_length",
                        "score_style_cs",
                        "score_style_ar",
                        "score_style_od",
                    ],
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully updated {all_user_stats.count()} user stats"
            )
        )

    def recalculate_memberships(
        self,
        memberships: QuerySet[Membership],
    ):
        paginator = Paginator(memberships.order_by("pk"), per_page=2000)

        with tqdm(desc="Memberships", total=memberships.count(), smoothing=0) as pbar:
            for page in paginator:
                for membership in page:
                    update_membership(membership.leaderboard, membership.user_id)
                    pbar.update()
                Membership.objects.bulk_update(page, ["pp"])

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully updated {memberships.count()} memberships"
            )
        )
