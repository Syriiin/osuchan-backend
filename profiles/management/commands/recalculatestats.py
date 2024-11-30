from django.core.management.base import BaseCommand
from django.core.paginator import Paginator
from django.db.models import QuerySet
from tqdm import tqdm

from common.osu.enums import Gamemode
from leaderboards.models import Membership
from leaderboards.services import update_membership
from profiles.models import UserStats


class Command(BaseCommand):
    help = "Recalculates user stats score styles and memberships"

    def add_arguments(self, parser):
        parser.add_argument(
            "--gamemode",
            type=int,
            help="Gamemode to recalculate stats for",
            choices=[Gamemode.STANDARD, Gamemode.TAIKO, Gamemode.CATCH, Gamemode.MANIA],
            required=True,
        )

    def handle(self, *args, **options):
        gamemode = Gamemode(options["gamemode"])

        # Recalculate user stats
        all_user_stats = UserStats.objects.filter(gamemode=gamemode)
        self.recalculate_user_stats(all_user_stats)

        # Recalculate memberships
        memberships = Membership.objects.select_related("leaderboard").filter(
            leaderboard__gamemode=gamemode
        )
        self.recalculate_memberships(memberships)

    def recalculate_user_stats(
        self,
        all_user_stats: QuerySet[UserStats],
    ):
        paginator = Paginator(all_user_stats.order_by("pk"), per_page=2000)

        with tqdm(desc="User Stats", total=all_user_stats.count(), smoothing=0) as pbar:
            for page in paginator:
                for user_stats in page:
                    user_stats.recalculate()
                    pbar.update()
                UserStats.objects.bulk_update(
                    page,
                    [
                        "extra_pp",
                        "score_style_accuracy",
                        "score_style_bpm",
                        "score_style_length",
                        "score_style_cs",
                        "score_style_ar",
                        "score_style_od",
                    ],
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully updated {all_user_stats.count()} user stats"
            )
        )

    def recalculate_memberships(
        self,
        memberships: QuerySet[Membership],
    ):
        paginator = Paginator(memberships.order_by("pk"), per_page=2000)

        with tqdm(desc="Memberships", total=memberships.count(), smoothing=0) as pbar:
            for page in paginator:
                for membership in page:
                    update_membership(
                        membership.leaderboard,
                        membership.user_id,
                        skip_notifications=True,
                    )
                    pbar.update()
                Membership.objects.bulk_update(page, ["pp"])

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully updated {memberships.count()} memberships"
            )
        )
