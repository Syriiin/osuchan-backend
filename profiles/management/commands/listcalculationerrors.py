from django.core.management.base import BaseCommand
from django.db.models import Count

from common.osu.difficultycalculator import (
    AbstractDifficultyCalculator,
    difficulty_calculators_classes,
)
from common.osu.enums import BeatmapStatus, Gamemode
from profiles.models import DifficultyCalculation, PerformanceCalculation


class Command(BaseCommand):
    help = "Displays errors in current calculations)"

    def handle(self, *args, **options):
        for name, difficulty_calculator_class in difficulty_calculators_classes.items():
            difficulty_calculator = difficulty_calculator_class()
            gamemode = difficulty_calculator.gamemode()

            self.stdout.write(
                "------------------------------------------------------------\n"
                f"Gamemode: {Gamemode(gamemode).name}\n"
                f"Difficulty Calculator: {name}\n"
                f"Difficulty Calculator Engine: {difficulty_calculator.engine()}\n"
                f"Difficulty Calculator Version: {difficulty_calculator.version()}\n"
            )

            self.output_errored_difficulty_calculations(difficulty_calculator)
            self.output_errored_performance_calculations(difficulty_calculator)

    def output_errored_difficulty_calculations(
        self, difficulty_calculator: AbstractDifficultyCalculator
    ):
        calculations = DifficultyCalculation.objects.filter(
            calculator_engine=difficulty_calculator.engine()
        )
        errored_difficulty_calculations = calculations.annotate(
            value_count=Count("difficulty_values")
        ).filter(value_count=0)

        if len(errored_difficulty_calculations) == 0:
            self.stdout.write(
                self.style.SUCCESS(f"No difficulty calculation errors found.")
            )
            return

        self.stdout.write(
            self.style.ERROR(
                f"Difficulty calculations errors: {len(errored_difficulty_calculations)}"
            )
        )

        errored_beatmap_set = set(
            calculation.beatmap for calculation in errored_difficulty_calculations
        )

        for beatmap in errored_beatmap_set:
            self.stdout.write(
                self.style.ERROR(
                    f"\t<{BeatmapStatus(beatmap.status).name}> {beatmap.id}: {beatmap}"
                )
            )

    def output_errored_performance_calculations(
        self, difficulty_calculator: AbstractDifficultyCalculator
    ):
        calculations = PerformanceCalculation.objects.filter(
            calculator_engine=difficulty_calculator.engine()
        )
        errored_performance_calculations = calculations.annotate(
            value_count=Count("performance_values")
        ).filter(value_count=0)

        if len(errored_performance_calculations) == 0:
            self.stdout.write(
                self.style.SUCCESS(f"No performance calculation errors found.")
            )
            return

        self.stdout.write(
            self.style.ERROR(
                f"Performance calculations errors: {len(errored_performance_calculations)}"
            )
        )

        errored_beatmap_set = set(
            calculation.score.beatmap
            for calculation in errored_performance_calculations
        )

        for beatmap in errored_beatmap_set:
            self.stdout.write(
                self.style.ERROR(
                    f"\t<{BeatmapStatus(beatmap.status).name}> {beatmap.id}: {beatmap}"
                )
            )
