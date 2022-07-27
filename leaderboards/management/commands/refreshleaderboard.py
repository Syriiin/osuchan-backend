from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from tqdm import tqdm

from leaderboards.enums import LeaderboardAccessType
from leaderboards.models import Leaderboard
from profiles.models import OsuUser


class Command(BaseCommand):
    help = "Updates memberships for the specified leaderboards"

    def add_arguments(self, parser):
        parser.add_argument("leaderboard_ids", nargs="+", type=int)

    def handle(self, *args, **options):
        for leaderboard_id in tqdm(options["leaderboard_ids"]):
            with transaction.atomic():
                try:
                    leaderboard = Leaderboard.objects.get(pk=leaderboard_id)
                except Leaderboard.DoesNotExist:
                    raise CommandError(f"Leaderboard {leaderboard_id} does not exist")

                if leaderboard.access_type == LeaderboardAccessType.GLOBAL:
                    users = OsuUser.objects.all().values("id")
                else:
                    users = leaderboard.members.all().values("id")
                for user_id in tqdm([u["id"] for u in users]):
                    leaderboard.update_membership(user_id)

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully refreshed {len(options['leaderboard_ids'])} leaderboard(s)"
            )
        )
