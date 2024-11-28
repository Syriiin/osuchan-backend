import time

from django.core.management.base import BaseCommand
from tqdm import tqdm

from common.osu.enums import Gamemode
from profiles.models import Score
from profiles.services import fetch_scores


class Command(BaseCommand):
    help = (
        "Calculates and populates score statistics for CL scores from legacy attributes"
    )

    def handle(self, *args, **options):
        self.refetch_lazer_scores_osu()
        self.refetch_lazer_scores_taiko()
        self.refetch_lazer_scores_catch()
        self.refetch_lazer_scores_mania()

    def refetch_lazer_scores_osu(self):
        scores = Score.objects.filter(
            gamemode=Gamemode.STANDARD, is_classic=False, statistics={}
        ).order_by("id")

        for score in tqdm(scores, desc="STANDARD", smoothing=0):
            # Sleep for 100ms to avoid rate limiting
            time.sleep(0.1)

            user_id = score.user_stats.user_id
            beatmap_id = score.beatmap_id
            gamemode = score.gamemode

            score.delete()
            fetch_scores(user_id, [beatmap_id], gamemode)

    def refetch_lazer_scores_taiko(self):
        scores = Score.objects.filter(
            gamemode=Gamemode.TAIKO, is_classic=False, statistics={}
        ).order_by("id")

        for score in tqdm(scores, desc="TAIKO", smoothing=0):
            # Sleep for 100ms to avoid rate limiting
            time.sleep(0.1)

            user_id = score.user_stats.user_id
            beatmap_id = score.beatmap_id
            gamemode = score.gamemode

            score.delete()
            fetch_scores(user_id, [beatmap_id], gamemode)

    def refetch_lazer_scores_catch(self):
        scores = Score.objects.filter(
            gamemode=Gamemode.CATCH, is_classic=False, statistics={}
        ).order_by("id")

        for score in tqdm(scores, desc="CATCH", smoothing=0):
            # Sleep for 100ms to avoid rate limiting
            time.sleep(0.1)

            user_id = score.user_stats.user_id
            beatmap_id = score.beatmap_id
            gamemode = score.gamemode

            score.delete()
            fetch_scores(user_id, [beatmap_id], gamemode)

    def refetch_lazer_scores_mania(self):
        scores = Score.objects.filter(
            gamemode=Gamemode.MANIA, is_classic=False, statistics={}
        ).order_by("id")

        for score in tqdm(scores, desc="MANIA", smoothing=0):
            # Sleep for 100ms to avoid rate limiting
            time.sleep(0.1)

            user_id = score.user_stats.user_id
            beatmap_id = score.beatmap_id
            gamemode = score.gamemode

            score.delete()
            fetch_scores(user_id, [beatmap_id], gamemode)
