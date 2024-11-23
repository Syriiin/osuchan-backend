from django.core.management.base import BaseCommand
from django.core.paginator import Paginator
from tqdm import tqdm

from common.osu.enums import Gamemode
from profiles.models import Score


class Command(BaseCommand):
    help = (
        "Calculates and populates score statistics for CL scores from legacy attributes"
    )

    def handle(self, *args, **options):
        self.backfill_osu()
        self.backfill_taiko()
        self.backfill_catch()
        self.backfill_mania()

    def backfill_osu(self):
        scores = Score.objects.filter(
            gamemode=Gamemode.STANDARD, is_classic=True
        ).order_by("id")
        paginator = Paginator(scores, per_page=2000)

        with tqdm(desc="STANDARD", total=scores.count(), smoothing=0) as pbar:
            for page in paginator:
                for score in page:
                    statistics = {}
                    if score.count_300 != 0:
                        statistics["great"] = score.count_300
                    if score.count_100 != 0:
                        statistics["ok"] = score.count_100
                    if score.count_50 != 0:
                        statistics["meh"] = score.count_50
                    if score.count_miss != 0:
                        statistics["miss"] = score.count_miss
                    score.statistics = statistics

                Score.objects.bulk_update(page, ["statistics"])

                pbar.update(len(page))

    def backfill_taiko(self):
        scores = Score.objects.filter(
            gamemode=Gamemode.TAIKO, is_classic=True
        ).order_by("id")
        paginator = Paginator(scores, per_page=2000)

        with tqdm(desc="TAIKO", total=scores.count(), smoothing=0) as pbar:
            for page in paginator:
                for score in page:
                    statistics = {}
                    if score.count_300 != 0:
                        statistics["great"] = score.count_300
                    if score.count_100 != 0:
                        statistics["ok"] = score.count_100
                    if score.count_miss != 0:
                        statistics["miss"] = score.count_miss
                    score.statistics = statistics

                Score.objects.bulk_update(page, ["statistics"])

                pbar.update(len(page))

    def backfill_catch(self):
        scores = Score.objects.filter(
            gamemode=Gamemode.CATCH, is_classic=True
        ).order_by("id")
        paginator = Paginator(scores, per_page=2000)

        with tqdm(desc="CATCH", total=scores.count(), smoothing=0) as pbar:
            for page in paginator:
                for score in page:
                    statistics = {}
                    if score.count_300 != 0:
                        statistics["great"] = score.count_300
                    if score.count_miss != 0:
                        statistics["miss"] = score.count_miss
                    if score.count_100 != 0:
                        statistics["large_tick_hit"] = score.count_100
                    if score.count_50 != 0:
                        statistics["small_tick_hit"] = score.count_50
                    if score.count_katu != 0:
                        statistics["small_tick_miss"] = score.count_katu
                    score.statistics = statistics

                Score.objects.bulk_update(page, ["statistics"])

                pbar.update(len(page))

    def backfill_mania(self):
        scores = Score.objects.filter(
            gamemode=Gamemode.MANIA, is_classic=True
        ).order_by("id")
        paginator = Paginator(scores, per_page=2000)

        with tqdm(desc="MANIA", total=scores.count(), smoothing=0) as pbar:
            for page in paginator:
                for score in page:
                    statistics = {}
                    if score.count_geki != 0:
                        statistics["perfect"] = score.count_geki
                    if score.count_300 != 0:
                        statistics["great"] = score.count_300
                    if score.count_katu != 0:
                        statistics["good"] = score.count_katu
                    if score.count_100 != 0:
                        statistics["ok"] = score.count_100
                    if score.count_50 != 0:
                        statistics["meh"] = score.count_50
                    if score.count_miss != 0:
                        statistics["miss"] = score.count_miss
                    score.statistics = statistics

                Score.objects.bulk_update(page, ["statistics"])

                pbar.update(len(page))
