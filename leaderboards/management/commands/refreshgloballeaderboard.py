from django.core.management.base import BaseCommand, CommandError
from tqdm import tqdm

from leaderboards.models import Leaderboard
from profiles.models import OsuUser


class Command(BaseCommand):
    help = "Refreshes the specified global leaderboards for all users"

    def add_arguments(self, parser):
        parser.add_argument("leaderboard_ids", nargs="+", type=int)

    def handle(self, *args, **options):
        osu_users = OsuUser.objects.all().values("id")
        for leaderboard_id in options["leaderboard_ids"]:
            try:
                leaderboard = Leaderboard.global_leaderboards.get(pk=leaderboard_id)
            except Leaderboard.DoesNotExist:
                raise CommandError(
                    f"Global leaderboard {leaderboard_id} does not exist"
                )

            # Refresh leaderboard
            for osu_user in tqdm(osu_users):
                leaderboard.update_membership(osu_user["id"])

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully refreshed leaderboard {leaderboard_id}"
                )
            )
