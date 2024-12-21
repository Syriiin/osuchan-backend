from django.core.management.base import BaseCommand
from django.core.paginator import Paginator
from tqdm import tqdm

from common.osu.utils import get_json_mods
from profiles.models import Score


class Command(BaseCommand):
    help = "Generates json mods for stable scores from legacy attributes"

    def handle(self, *args, **options):
        scores = Score.objects.filter(is_stable=True).order_by("id")
        paginator = Paginator(scores, per_page=2000)

        with tqdm(total=scores.count(), smoothing=0) as pbar:
            for page in paginator:
                for score in page:
                    score.mods_json = get_json_mods(score.mods, score.is_stable)
                    pbar.update()

                Score.objects.bulk_update(page, ["mods_json"])
