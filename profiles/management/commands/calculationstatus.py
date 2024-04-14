from django.core.management.base import BaseCommand
from django.db.models import QuerySet

from common.osu.difficultycalculator import DifficultyCalculator
from common.osu.enums import Gamemode
from profiles.models import Beatmap, Score


class Command(BaseCommand):
    help = "Displays current db calculation status"

    def add_arguments(self, parser):
        parser.add_argument(
            "--v2",
            action="store_true",
            help="Use new difficulty and performance models",
        )

    def handle(self, *args, **options):
        # the v2 flag is used to determine whether to use the new difficulty and performance models
        v2 = options["v2"]

        # TODO: iterate over supported gamemodes
        gamemode = Gamemode.STANDARD

        self.stdout.write(
            f"Gamemode: {Gamemode(gamemode).name}\n"
            f"Difficulty Calculator Engine: {DifficultyCalculator.engine()}\n"
            f"Difficulty Calculator Version: {DifficultyCalculator.version()}\n"
        )

        if v2:
            beatmaps = Beatmap.objects.filter(gamemode=gamemode)
            outdated_beatmap_count = self.get_outdated_beatmap_count_v2(beatmaps)

            scores = Score.objects.filter(gamemode=gamemode)
            outdated_score_count = self.get_outdated_score_count_v2(scores)
        else:
            beatmaps = Beatmap.objects.filter(gamemode=gamemode)
            outdated_beatmap_count = self.get_outdated_beatmap_count(beatmaps)

            scores = Score.objects.filter(gamemode=gamemode)
            outdated_score_count = self.get_outdated_score_count(scores)

        beatmap_count = beatmaps.count()
        up_to_date_beatmap_count = beatmap_count - outdated_beatmap_count

        score_count = scores.count()
        up_to_date_score_count = score_count - outdated_score_count

        if up_to_date_beatmap_count == 0:
            beatmap_output_style = self.style.ERROR
        elif up_to_date_beatmap_count == beatmap_count:
            beatmap_output_style = self.style.SUCCESS
        else:
            beatmap_output_style = self.style.WARNING

        if up_to_date_score_count == 0:
            score_output_style = self.style.ERROR
        elif up_to_date_score_count == score_count:
            score_output_style = self.style.SUCCESS
        else:
            score_output_style = self.style.WARNING

        self.stdout.write(
            beatmap_output_style(
                f"Up-to-date Beatmaps: {up_to_date_beatmap_count} / {beatmap_count} ({(up_to_date_beatmap_count / beatmap_count) * 100:.2f}%)"
            )
        )
        self.stdout.write(
            score_output_style(
                f"Up-to-date Scores: {up_to_date_score_count} / {score_count} ({(up_to_date_score_count / score_count) * 100:.2f}%)"
            )
        )

    def get_outdated_beatmap_count(self, beatmaps: QuerySet[Beatmap]):
        beatmaps_to_recalculate = beatmaps.exclude(
            difficulty_calculator_engine=DifficultyCalculator.engine(),
            difficulty_calculator_version=DifficultyCalculator.version(),
        ).order_by("pk")

        return beatmaps_to_recalculate.count()

    def get_outdated_score_count(self, scores: QuerySet[Score]):
        scores_to_recalculate = scores.exclude(
            difficulty_calculator_engine=DifficultyCalculator.engine(),
            difficulty_calculator_version=DifficultyCalculator.version(),
        ).order_by("pk")

        return scores_to_recalculate.count()

    def get_outdated_beatmap_count_v2(self, beatmaps: QuerySet[Beatmap]):
        beatmaps_to_recalculate = beatmaps.exclude(
            difficulty_calculations__calculator_engine=DifficultyCalculator.engine(),
            difficulty_calculations__calculator_version=DifficultyCalculator.version(),
        )

        return beatmaps_to_recalculate.count()

    def get_outdated_score_count_v2(self, scores: QuerySet[Score]):
        scores_to_recalculate = scores.exclude(
            performance_calculations__calculator_engine=DifficultyCalculator.engine(),
            performance_calculations__calculator_version=DifficultyCalculator.version(),
        )

        return scores_to_recalculate.count()
