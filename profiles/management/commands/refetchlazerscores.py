import time

from django.core.management.base import BaseCommand
from tqdm import tqdm

from common.osu.enums import Gamemode
from profiles.models import UserStats
from profiles.services import fetch_scores


class Command(BaseCommand):
    help = (
        "Calculates and populates score statistics for CL scores from legacy attributes"
    )

    def handle(self, *args, **options):
        self.refetch_lazer_scores(Gamemode.STANDARD)
        self.refetch_lazer_scores(Gamemode.TAIKO)
        self.refetch_lazer_scores(Gamemode.CATCH)
        self.refetch_lazer_scores(Gamemode.MANIA)

    def refetch_lazer_scores(self, gamemode: Gamemode):
        user_stats = UserStats.objects.filter(gamemode=gamemode).order_by("id")

        for stats in tqdm(user_stats, desc=gamemode.name, smoothing=0):
            # Sleep for 100ms to avoid rate limiting
            time.sleep(0.1)

            beatmap_ids = list(
                stats.scores.filter(is_classic=False)
                .values_list("beatmap_id", flat=True)
                .distinct()
            )
            stats.scores.filter(beatmap_id__in=beatmap_ids, is_classic=False).delete()

            fetch_scores(stats.user_id, beatmap_ids, gamemode)
