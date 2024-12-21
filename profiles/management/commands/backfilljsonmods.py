from django.core.management.base import BaseCommand
from tqdm import tqdm

from common.osu.utils import get_mod_acronyms
from profiles.models import ScoreFilter


class Command(BaseCommand):
    help = "Generates json mods for all ScoreFilters"

    def handle(self, *args, **options):
        score_filters = ScoreFilter.objects.all()
        for score_filter in tqdm(score_filters):
            score_filter.required_mods_json = get_mod_acronyms(
                score_filter.required_mods
            )
            score_filter.disqualified_mods_json = get_mod_acronyms(
                score_filter.disqualified_mods
            )
            score_filter.save()
