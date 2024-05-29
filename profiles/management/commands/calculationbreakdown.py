from django.core.management.base import BaseCommand
from django.db.models import Count

from common.osu.difficultycalculator import (
    AbstractDifficultyCalculator,
    difficulty_calculators,
)
from common.osu.enums import Gamemode
from profiles.models import (
    Beatmap,
    DifficultyCalculation,
    PerformanceCalculation,
    Score,
)


class Command(BaseCommand):
    help = "Displays current db calculation breakdown (new models)"

    def handle(self, *args, **options):
        for name, difficulty_calculator_class in difficulty_calculators.items():
            difficulty_calculator = difficulty_calculator_class()
            gamemode = difficulty_calculator.gamemode()

            self.stdout.write(
                "------------------------------------------------------------\n"
                f"Gamemode: {Gamemode(gamemode).name}\n"
                f"Difficulty Calculator: {name}\n"
                f"Difficulty Calculator Engine: {difficulty_calculator.engine()}\n"
                f"Difficulty Calculator Version: {difficulty_calculator.version()}\n"
            )

            self.output_beatmap_version_counts(difficulty_calculator)
            self.output_score_version_counts(difficulty_calculator)

    def output_beatmap_version_counts(
        self, difficulty_calculator: AbstractDifficultyCalculator
    ):
        beatmaps = Beatmap.objects.filter(gamemode=difficulty_calculator.gamemode())
        beatmap_count = beatmaps.count()

        self.stdout.write(f"Beatmaps:")

        difficulty_calculations = DifficultyCalculation.objects.filter(
            beatmap__gamemode=difficulty_calculator.gamemode(),  # TODO: remove this? shouldnt be needed since calc engine implies gamemode
            mods=0,
            calculator_engine=difficulty_calculator.engine(),
        )

        version_counts = difficulty_calculations.values("calculator_version").annotate(
            count=Count("id")
        )

        for diffcalc_count in version_counts:
            self.stdout.write(
                f"\t{diffcalc_count['calculator_version']}: {self.output_count(diffcalc_count['count'], beatmap_count)}"
            )

        uncalculated_count = beatmap_count - sum(
            diffcalc_count["count"] for diffcalc_count in version_counts
        )
        if uncalculated_count > 0:
            self.stdout.write(
                f"\tUncalculated: {self.style.ERROR(f'{uncalculated_count} / {beatmap_count} ({(uncalculated_count / beatmap_count) * 100:.2f}%)')}"
            )

    def output_score_version_counts(
        self, difficulty_calculator: AbstractDifficultyCalculator
    ):
        scores = Score.objects.filter(gamemode=difficulty_calculator.gamemode())
        score_count = scores.count()

        self.stdout.write(f"Scores:")

        performance_calculations = PerformanceCalculation.objects.filter(
            score__gamemode=difficulty_calculator.gamemode(),
            calculator_engine=difficulty_calculator.engine(),
        )

        version_counts = performance_calculations.values("calculator_version").annotate(
            count=Count("id")
        )

        for diffcalc_count in version_counts:
            self.stdout.write(
                f"\t{diffcalc_count['calculator_version']}: {self.output_count(diffcalc_count['count'], score_count)}"
            )

        uncalculated_count = score_count - sum(
            diffcalc_count["count"] for diffcalc_count in version_counts
        )
        if uncalculated_count > 0:
            self.stdout.write(
                f"\tUncalculated: {self.style.ERROR(f'{uncalculated_count} / {score_count} ({(uncalculated_count / score_count) * 100:.2f}%)')}"
            )

    def output_count(self, count: int, total: int):
        if count == 0:
            return self.style.ERROR(f"{count} / {total} (0.00%)")
        elif count == total:
            return self.style.SUCCESS(f"{count} / {total} (100.00%)")
        else:
            return self.style.WARNING(
                f"{count} / {total} ({(count / total) * 100:.2f}%)"
            )
