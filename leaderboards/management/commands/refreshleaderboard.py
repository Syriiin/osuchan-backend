from django.core.management.base import BaseCommand, CommandError
from tqdm import tqdm

from leaderboards.enums import LeaderboardAccessType
from leaderboards.models import Leaderboard
from leaderboards.services import reconcile_member_top_scores, update_membership
from profiles.models import OsuUser


class Command(BaseCommand):
    help = "Updates memberships for the specified leaderboards"

    def add_arguments(self, parser):
        parser.add_argument("leaderboard_ids", nargs="+", type=int)

    def handle(self, *args, **options):
        for leaderboard_id in tqdm(options["leaderboard_ids"]):
            try:
                leaderboard = Leaderboard.objects.get(pk=leaderboard_id)
            except Leaderboard.DoesNotExist:
                raise CommandError(f"Leaderboard {leaderboard_id} does not exist")

            if leaderboard.access_type == LeaderboardAccessType.GLOBAL:
                users = OsuUser.objects.all().values("id")
            else:
                users = leaderboard.members.all().values("id")
            for user_id in tqdm([u["id"] for u in users]):
                update_membership(
                    leaderboard,
                    user_id,
                    skip_notifications=True,
                    skip_top_scores_update=True,
                )
                reconcile_member_top_scores(leaderboard.id, user_id)

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully refreshed {len(options['leaderboard_ids'])} leaderboard(s)"
            )
        )
