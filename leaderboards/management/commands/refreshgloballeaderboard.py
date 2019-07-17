from django.db import transaction
from django.core.management.base import BaseCommand, CommandError

from profiles.models import OsuUser
from leaderboards.models import Leaderboard, Membership
from leaderboards.enums import LeaderboardAccessType

class Command(BaseCommand):
    help = "Refreshes the specified global leaderboards for all users"

    def add_arguments(self, parser):
        parser.add_argument("leaderboard_ids", nargs="+", type=int)

    def handle(self, *args, **options):
        osu_users = OsuUser.objects.all().values("id")
        for leaderboard_id in options["leaderboard_ids"]:
            try:
                leaderboard = Leaderboard.objects.get(pk=leaderboard_id, access_type=LeaderboardAccessType.GLOBAL)
            except Leaderboard.DoesNotExist:
                raise CommandError(f"Global leaderboard {leaderboard_id} does not exist")

            # Refresh leaderboard
            with transaction.atomic():
                for osu_user in osu_users:
                    leaderboard.update_membership(osu_user["id"])

            self.stdout.write(self.style.SUCCESS(f"Successfully refreshed leaderboard {leaderboard_id}"))
