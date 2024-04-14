from typing import Iterable

from django.core.management.base import BaseCommand
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, QuerySet
from tqdm import tqdm

from common.osu.difficultycalculator import DifficultyCalculator
from common.osu.enums import Gamemode, Mods
from leaderboards.models import Membership
from profiles.models import (
    Beatmap,
    DifficultyCalculation,
    DifficultyValue,
    PerformanceCalculation,
    PerformanceValue,
    Score,
    UserStats,
)


class Command(BaseCommand):
    help = "Recalculates beatmap difficulty values, score performance values and user stats score styles"

    def add_arguments(self, parser):
        parser.add_argument("gamemode", nargs=1, type=int)
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force recalculation of beatmaps and scores even if already up to date",
        )
        parser.add_argument(
            "--v2",
            action="store_true",
            help="Use new difficulty and performance models",
        )

    def handle(self, *args, **options):
        gamemode = options["gamemode"][0]
        force = options["force"]
        # the v2 flag is used to determine whether to use the new difficulty and performance models
        v2 = options["v2"]

        if gamemode != Gamemode.STANDARD:
            self.stdout.write(
                self.style.ERROR(
                    f"Gamemode {gamemode} is current not supported for difficulty calculations"
                )
            )
            return

        self.stdout.write(
            f"Gamemode: {Gamemode(gamemode).name}\n"
            f"Difficulty Calculator Engine: {DifficultyCalculator.engine()}\n"
            f"Difficulty Calculator Version: {DifficultyCalculator.version()}\n"
        )

        if v2:
            # Recalculate beatmaps
            beatmaps = Beatmap.objects.filter(gamemode=gamemode)
            self.recalculate_beatmaps_v2(beatmaps, force)

            # Recalculate scores
            scores = Score.objects.filter(gamemode=gamemode)
            self.recalculate_scores_v2(scores, force)
        else:
            # Recalculate beatmaps
            beatmaps = Beatmap.objects.filter(gamemode=gamemode)
            self.recalculate_beatmaps(beatmaps, force)

            # Recalculate scores
            scores = Score.objects.filter(gamemode=gamemode)
            self.recalculate_scores(scores, force)

        # Recalculate user stats
        all_user_stats = UserStats.objects.filter(gamemode=gamemode)
        self.recalculate_user_stats(all_user_stats)

        # Recalculate memberships
        memberships = Membership.objects.select_related("leaderboard").filter(
            leaderboard__gamemode=gamemode
        )
        self.recalculate_memberships(memberships)

    def recalculate_beatmap_page(self, page: Iterable[Beatmap], progress_bar: tqdm):
        for beatmap in page:
            beatmap.update_difficulty_values(DifficultyCalculator)
            progress_bar.update()

        Beatmap.objects.bulk_update(
            page,
            [
                "difficulty_total",
                "difficulty_calculator_engine",
                "difficulty_calculator_version",
            ],
        )

    def recalculate_beatmaps(self, beatmaps: QuerySet[Beatmap], force: bool = False):
        if force:
            self.stdout.write(f"Forcing recalculation of all beatmaps...")

            paginator = Paginator(beatmaps.order_by("pk"), per_page=2000)

            with tqdm(desc="Beatmaps", total=beatmaps.count(), smoothing=0) as pbar:
                for page in paginator:
                    self.recalculate_beatmap_page(page, pbar)
        else:
            beatmaps_to_recalculate = beatmaps.exclude(
                difficulty_calculator_engine=DifficultyCalculator.engine(),
                difficulty_calculator_version=DifficultyCalculator.version(),
            ).order_by("pk")

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
                    self.recalculate_beatmap_page(page, pbar)

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully updated {beatmaps.count()} beatmaps' difficulty values"
            )
        )

    def recalculate_score_page(self, page: Iterable[Score], progress_bar: tqdm):
        for score in page:
            score.update_performance_values(DifficultyCalculator)
            progress_bar.update()

        Score.objects.bulk_update(
            page,
            [
                "nochoke_performance_total",
                "difficulty_total",
                "difficulty_calculator_engine",
                "difficulty_calculator_version",
                "performance_total",
            ],
        )

    def recalculate_scores(self, scores: QuerySet[Score], force: bool = False):
        if force:
            self.stdout.write(f"Forcing recalculation of all scores...")

            paginator = Paginator(scores.order_by("pk"), per_page=2000)

            with tqdm(desc="Scores", total=scores.count(), smoothing=0) as pbar:
                for page in paginator:
                    self.recalculate_score_page(page, pbar)
        else:
            scores_to_recalculate = scores.exclude(
                difficulty_calculator_engine=DifficultyCalculator.engine(),
                difficulty_calculator_version=DifficultyCalculator.version(),
            ).order_by("pk")

            if scores_to_recalculate.count() == 0:
                self.stdout.write(f"All {scores.count()} scores already up to date")
                return

            count_up_to_date = scores.count() - scores_to_recalculate.count()

            if count_up_to_date > 0:
                self.stdout.write(
                    f"Found {count_up_to_date} scores already up to date. Resuming..."
                )

            with tqdm(
                desc="Scores",
                total=scores.count(),
                initial=count_up_to_date,
                smoothing=0,
            ) as pbar:
                while len(page := scores_to_recalculate[:2000]) > 0:
                    self.recalculate_score_page(page, pbar)

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully updated {scores.count()} scores' performance values"
            )
        )

    def recalculate_beatmaps_v2(self, beatmaps: QuerySet[Beatmap], force: bool = False):
        if force:
            self.stdout.write(f"Forcing recalculation of all beatmaps...")

            paginator = Paginator(beatmaps.order_by("pk"), per_page=2000)

            with tqdm(desc="Beatmaps", total=beatmaps.count(), smoothing=0) as pbar:
                for page in paginator:
                    self.recalculate_beatmap_page_v2(page, pbar)
        else:
            beatmaps_to_recalculate = beatmaps.exclude(
                difficulty_calculations__calculator_engine=DifficultyCalculator.engine(),
                difficulty_calculations__calculator_version=DifficultyCalculator.version(),
            )

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
                    self.recalculate_beatmap_page_v2(page, pbar)

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully updated {beatmaps.count()} beatmaps' difficulty values"
            )
        )

    @transaction.atomic
    def recalculate_beatmap_page_v2(self, page: Iterable[Beatmap], progress_bar: tqdm):
        calculations = []
        beatmap_ids = []
        for beatmap in page:
            calculations.append(
                DifficultyCalculation(
                    beatmap_id=beatmap.id,
                    mods=Mods.NONE,
                    calculator_engine=DifficultyCalculator.engine(),
                    calculator_version=DifficultyCalculator.version(),
                )
            )
            beatmap_ids.append(beatmap.id)

        # Create calculations
        DifficultyCalculation.objects.bulk_create(calculations, ignore_conflicts=True)
        calculations = DifficultyCalculation.objects.filter(
            beatmap_id__in=beatmap_ids,
            mods=Mods.NONE,
            calculator_engine=DifficultyCalculator.engine(),
            calculator_version=DifficultyCalculator.version(),
        )

        # Perform calculations
        values = []
        for calculation in calculations:
            values.extend(calculation.calculate_difficulty_values(DifficultyCalculator))
            progress_bar.update()

        # Create values
        DifficultyValue.objects.bulk_create(
            values,
            update_conflicts=True,
            update_fields=["value"],
            unique_fields=["calculation_id", "name"],
        )

    def recalculate_scores_v2(self, scores: QuerySet[Score], force: bool = False):
        if force:
            self.stdout.write(f"Forcing recalculation of all scores...")

            scores_to_recalculate = scores
            initial = 0
        else:
            scores_to_recalculate = scores.exclude(
                performance_calculations__calculator_engine=DifficultyCalculator.engine(),
                performance_calculations__calculator_version=DifficultyCalculator.version(),
            )

            if scores_to_recalculate.count() == 0:
                self.stdout.write(f"All {scores.count()} scores already up to date")
                return

            count_up_to_date = scores.count() - scores_to_recalculate.count()

            if count_up_to_date > 0:
                self.stdout.write(
                    f"Found {count_up_to_date} scores already up to date. Resuming..."
                )

            initial = count_up_to_date

        unique_beatmaps = (
            scores_to_recalculate.values("beatmap_id", "mods")
            .annotate(count=Count("*"))
            .order_by("-count")
        )

        with tqdm(
            desc="Scores",
            total=scores.count(),
            initial=initial,
            smoothing=0,
        ) as pbar:
            for unique_beatmap in unique_beatmaps:
                unique_beatmap_scores = scores_to_recalculate.filter(
                    beatmap_id=unique_beatmap["beatmap_id"], mods=unique_beatmap["mods"]
                )
                self.recalculate_scores_for_unique_beatmap_v2(
                    unique_beatmap["beatmap_id"],
                    unique_beatmap["mods"],
                    unique_beatmap_scores,
                    pbar,
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully updated {scores.count()} scores' performance values"
            )
        )

    @transaction.atomic
    def recalculate_scores_for_unique_beatmap_v2(
        self, beatmap_id: int, mods: int, scores: Iterable[Score], progress_bar: tqdm
    ):
        # Validate all scores are of same beatmap/mods
        for score in scores:
            if score.beatmap_id != beatmap_id or score.mods != mods:
                raise Exception(
                    f"Score {score.id} does not match beatmap {beatmap_id} and mods {mods}"
                )

        # Create difficulty calculation
        difficulty_calculation, _ = DifficultyCalculation.objects.get_or_create(
            beatmap_id=beatmap_id,
            mods=mods,
            calculator_engine=DifficultyCalculator.engine(),
            calculator_version=DifficultyCalculator.version(),
        )

        # Do difficulty calculation
        difficulty_values = difficulty_calculation.calculate_difficulty_values(
            DifficultyCalculator
        )
        DifficultyValue.objects.bulk_create(
            difficulty_values,
            update_conflicts=True,
            update_fields=["value"],
            unique_fields=["calculation_id", "name"],
        )

        score_dict = {}
        performance_calculations = []
        for score in scores:
            performance_calculations.append(
                PerformanceCalculation(
                    score_id=score.id,
                    difficulty_calculation_id=difficulty_calculation.id,
                    calculator_engine=DifficultyCalculator.engine(),
                    calculator_version=DifficultyCalculator.version(),
                )
            )
            score_dict[score.id] = score

        # Create calculations
        PerformanceCalculation.objects.bulk_create(
            performance_calculations, ignore_conflicts=True
        )
        performance_calculations = PerformanceCalculation.objects.filter(
            score_id__in=score_dict.keys(),
            calculator_engine=DifficultyCalculator.engine(),
            calculator_version=DifficultyCalculator.version(),
        )

        # Perform calculations
        values = []
        for calculation in performance_calculations:
            values.extend(
                calculation.calculate_performance_values(
                    score_dict[calculation.score_id], DifficultyCalculator
                )
            )
            progress_bar.update()

        # Create values
        PerformanceValue.objects.bulk_create(
            values,
            update_conflicts=True,
            update_fields=["value"],
            unique_fields=["calculation_id", "name"],
        )

    def recalculate_user_stats(self, all_user_stats: QuerySet[UserStats]):
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

    def recalculate_memberships(self, memberships: QuerySet[Membership]):
        paginator = Paginator(memberships.order_by("pk"), per_page=2000)

        with tqdm(desc="Memberships", total=memberships.count(), smoothing=0) as pbar:
            for page in paginator:
                for membership in page:
                    membership.recalculate()
                    pbar.update()
                Membership.objects.bulk_update(page, ["pp"])

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully updated {memberships.count()} memberships"
            )
        )
