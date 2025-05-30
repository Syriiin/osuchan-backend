from django.core.management.base import BaseCommand
from django.core.paginator import Paginator
from django.db.models import FilteredRelation, Q, QuerySet
from tqdm import tqdm

from common.error_reporter import ErrorReporter
from common.osu.difficultycalculator import (
    CalculationException,
    get_default_difficulty_calculator_class,
)
from common.osu.enums import Gamemode
from profiles.models import Beatmap


class Command(BaseCommand):
    help = "Calculates hitobject counts for all Beatmaps"

    def handle(self, *args, **options):
        self.backfill_gamemode_hitobject_counts(
            Gamemode.STANDARD, Beatmap.objects.filter(gamemode=Gamemode.STANDARD)
        )
        self.backfill_gamemode_hitobject_counts(
            Gamemode.TAIKO, Beatmap.objects.filter(gamemode=Gamemode.TAIKO)
        )
        self.backfill_gamemode_hitobject_counts(
            Gamemode.CATCH, Beatmap.objects.filter(gamemode=Gamemode.CATCH)
        )
        self.backfill_gamemode_hitobject_counts(
            Gamemode.MANIA, Beatmap.objects.filter(gamemode=Gamemode.MANIA)
        )

        self.stdout.write(
            self.style.SUCCESS("Hitobject counts backfilled successfully.")
        )

    def backfill_gamemode_hitobject_counts(
        self, gamemode: Gamemode, beatmaps: QuerySet[Beatmap]
    ):
        difficulty_calculator = get_default_difficulty_calculator_class(gamemode)()
        with tqdm(desc=gamemode.name, total=beatmaps.count()) as pbar:
            paginator = Paginator(beatmaps.order_by("pk"), per_page=2000)

            for page in paginator:
                for beatmap in page:
                    try:
                        beatmap_details = difficulty_calculator.get_beatmap_details(
                            str(beatmap.id)
                        )
                        beatmap.hitobject_counts = beatmap_details.hitobject_counts
                    except CalculationException as e:
                        ErrorReporter().report_error(e)
                        pbar.write(
                            f"Error calculating hitobject counts for beatmap {beatmap.id} in gamemode {gamemode.name}: {e}"
                        )

                    pbar.update(1)

                Beatmap.objects.bulk_update(page, ["hitobject_counts"])
