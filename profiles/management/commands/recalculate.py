from django.core.management.base import BaseCommand
from django.core.paginator import Paginator
from django.db.models import QuerySet
from tqdm import tqdm

from common.osu.difficultycalculator import RosuppDifficultyCalculator
from common.osu.enums import Gamemode
from profiles.models import Beatmap, Score, UserStats


class Command(BaseCommand):
    help = "Recalculates beatmap difficulty values, score performance values and user stats score styles"

    def add_arguments(self, parser):
        parser.add_argument("gamemode", nargs=1, type=int)

    def handle(self, *args, **options):
        gamemode = options["gamemode"][0]

        if gamemode != Gamemode.STANDARD:
            self.stdout.write(
                self.style.ERROR(
                    f"Gamemode {gamemode} is current not supported for difficulty calculations"
                )
            )
            return

        # Recalculate beatmaps
        beatmaps = Beatmap.objects.filter(gamemode=gamemode)

        self.recalculate_beatmaps(beatmaps)

        # Recalculate scores

        scores = Score.objects.filter(gamemode=gamemode)

        self.recalculate_scores(scores)

        # Recalculate user stats

        all_user_stats = UserStats.objects.filter(gamemode=gamemode)

        self.recalculate_user_stats(all_user_stats)

    def recalculate_beatmaps(self, beatmaps: QuerySet[Beatmap]):
        paginator = Paginator(beatmaps.order_by("pk"), per_page=2000)

        with tqdm(desc="Beatmaps", total=beatmaps.count()) as pbar:
            for page in paginator:
                for beatmap in page:
                    beatmap.update_difficulty_values(RosuppDifficultyCalculator)
                    pbar.update()

                Beatmap.objects.bulk_update(
                    page.object_list,
                    [
                        "difficulty_total",
                        "difficulty_calculator_engine",
                        "difficulty_calculator_version",
                    ],
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully updated {beatmaps.count()} beatmaps' difficulty values"
            )
        )

    def recalculate_scores(self, scores: QuerySet[Score]):
        paginator = Paginator(scores.order_by("pk"), per_page=2000)

        with tqdm(desc="Scores", total=scores.count()) as pbar:
            for page in paginator:
                for score in page:
                    score.update_performance_values(RosuppDifficultyCalculator)
                    pbar.update()

                Score.objects.bulk_update(
                    page.object_list,
                    [
                        "nochoke_performance_total",
                        "difficulty_total",
                        "difficulty_calculator_engine",
                        "difficulty_calculator_version",
                        "performance_total",
                    ],
                )

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
