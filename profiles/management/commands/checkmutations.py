from django.core.management.base import BaseCommand
from django.db.models import F, FilteredRelation, Q, QuerySet
from tqdm import tqdm

from common.osu.difficultycalculator import get_difficulty_calculators_for_gamemode
from common.osu.enums import Gamemode
from profiles.enums import ScoreMutation, ScoreResult
from profiles.models import Score
from profiles.services import update_performance_calculations


class Command(BaseCommand):
    help = "Checks all scores have required mutations created."

    def add_arguments(self, parser):
        parser.add_argument(
            "--fix",
            action="store_true",
            help="Whether create missing mutations after detecting them",
        )

    def handle(self, *args, **options):
        fix = options["fix"]
        gamemode = Gamemode.STANDARD
        self.check_nochoke_mutations(gamemode, fix)

    def check_nochoke_mutations(
        self, gamemode: Gamemode, create_missing_mutations: bool
    ):
        choke_scores = Score.objects.filter_mutations().filter(
            result=F("result").bitand(ScoreResult.CHOKE)
        )

        choke_scores_missing_nochoke_mutation = (
            Score.objects.filter_mutations()
            .filter(gamemode=gamemode, result=F("result").bitand(ScoreResult.CHOKE))
            .annotate(
                nochoke_mutation=FilteredRelation(
                    "mutations",
                    condition=Q(mutations__mutation=ScoreMutation.NO_CHOKE),
                )
            )
            .filter(nochoke_mutation=None)
        )

        total_count = choke_scores.count()
        missing_count = choke_scores_missing_nochoke_mutation.count()

        if missing_count == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f"All {total_count} choke scores have nochoke mutations created"
                )
            )
            return

        self.stdout.write(
            self.style.ERROR(
                f"{missing_count} / {total_count} choke scores are missing nochoke mutations ({(total_count - missing_count) / total_count * 100:.2f}% complete)"
            )
        )
        if create_missing_mutations:
            self.create_missing_nochoke_mutations(
                gamemode, choke_scores_missing_nochoke_mutation
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created {missing_count} missing nochoke mutations for choke scores"
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    "Use --fix to create missing mutations for choke scores"
                )
            )

    def create_missing_nochoke_mutations(
        self, gamemode: Gamemode, choke_scores: QuerySet[Score]
    ):
        with tqdm(
            desc="No-choke", total=choke_scores.count(), smoothing=0
        ) as progress_bar:
            while len(page := choke_scores.select_related("beatmap")[:2000]) > 0:
                self.create_missing_nochoke_mutations_page(gamemode, page)
                progress_bar.update(len(page))

    def create_missing_nochoke_mutations_page(
        self, gamemode: Gamemode, choke_scores: QuerySet[Score]
    ):
        scores_to_create = []
        for score in choke_scores:
            scores_to_create.append(score.get_nochoke_mutation())
        created_scores = Score.objects.bulk_create(scores_to_create)

        for difficulty_calculator_class in get_difficulty_calculators_for_gamemode(
            gamemode
        ):
            with difficulty_calculator_class() as difficulty_calculator:
                update_performance_calculations(created_scores, difficulty_calculator)
