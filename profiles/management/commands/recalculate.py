from typing import Iterable

from django.core.management.base import BaseCommand
from django.core.paginator import Paginator
from django.db.models import QuerySet
from tqdm import tqdm

from common.osu.difficultycalculator import DifficultyCalculator
from common.osu.enums import Gamemode
from profiles.models import Beatmap, Score, UserStats


class Command(BaseCommand):
    help = "Recalculates beatmap difficulty values, score performance values and user stats score styles"

    def add_arguments(self, parser):
        parser.add_argument("gamemode", nargs=1, type=int)
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force recalculation of beatmaps and scores even if already up to date",
        )

    def handle(self, *args, **options):
        gamemode = options["gamemode"][0]
        force = options["force"]

        if gamemode != Gamemode.STANDARD:
            self.stdout.write(
                self.style.ERROR(
                    f"Gamemode {gamemode} is current not supported for difficulty calculations"
                )
            )
            return

        # Recalculate beatmaps
        beatmaps = Beatmap.objects.filter(gamemode=gamemode)

        self.recalculate_beatmaps(beatmaps, force)

        # Recalculate scores

        scores = Score.objects.filter(gamemode=gamemode)

        self.recalculate_scores(scores, force)

        # Recalculate user stats

        all_user_stats = UserStats.objects.filter(gamemode=gamemode)

        self.recalculate_user_stats(all_user_stats)

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

            with tqdm(desc="Beatmaps", total=beatmaps.count()) as pbar:
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
                desc="Beatmaps", total=beatmaps.count(), initial=count_up_to_date
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

            with tqdm(desc="Scores", total=scores.count()) as pbar:
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
                desc="Scores", total=scores.count(), initial=count_up_to_date
            ) as pbar:
                while len(page := scores_to_recalculate[:2000]) > 0:
                    self.recalculate_score_page(page, pbar)

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully updated {scores.count()} scores' performance values"
            )
        )

    def recalculate_user_stats(self, all_user_stats: QuerySet[UserStats]):
        for user_stats in tqdm(
            all_user_stats.iterator(), desc="User Stats", total=all_user_stats.count()
        ):
            user_stats.recalculate()
            user_stats.save()

            # TODO: update memberships

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully updated {all_user_stats.count()} user stats"
            )
        )
