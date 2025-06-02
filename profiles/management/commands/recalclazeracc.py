from django.core.management.base import BaseCommand
from django.core.paginator import Paginator
from tqdm import tqdm

from common.osu import utils
from common.osu.enums import Gamemode
from profiles.models import Score


class Command(BaseCommand):
    help = "Recalculate accuracy for all lazer scores."

    def handle(self, *args, **options):
        self.recalculate_lazer_acc(Gamemode.STANDARD)
        self.recalculate_lazer_acc(Gamemode.TAIKO)
        self.recalculate_lazer_acc(Gamemode.CATCH)
        self.recalculate_lazer_acc(Gamemode.MANIA)

        self.stdout.write(
            self.style.SUCCESS("Hitobject counts backfilled successfully.")
        )

    def recalculate_lazer_acc(self, gamemode: Gamemode):
        scores = (
            Score.objects.filter(gamemode=gamemode)
            .exclude(mods_json__has_any_keys=["CL"])
            .select_related("beatmap")
        )

        with tqdm(desc=gamemode.name, total=scores.count()) as pbar:
            paginator = Paginator(scores.order_by("pk"), per_page=2000)

            for page in paginator:
                for score in page:
                    score.accuracy = utils.get_lazer_accuracy(
                        score.statistics,
                        score.beatmap.hitobject_counts,
                        gamemode=gamemode,
                    )

                    pbar.update(1)

                Score.objects.bulk_update(page, ["accuracy"])
