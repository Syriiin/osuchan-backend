from django.db import transaction
from django.core.management.base import BaseCommand, CommandError

from osuauth.models import User

class Command(BaseCommand):
    help = "Refreshes the specified global leaderboards for all users"

    def add_arguments(self, parser):
        parser.add_argument("accept_count", nargs=1, type=int)
        parser.add_argument("accept_type", nargs=1, type=str)

    def handle(self, *args, **options):
        accept_count = options["accept_count"][0]
        accept_type = options["accept_type"][0]

        users = User.objects.filter(is_beta_tester=False)

        if accept_type == "random":
            users = users.order_by("?")
        else:
            users = users.order_by("date_joined")

        users = users[:accept_count]

        for user in users:
            user.is_beta_tester = True

        User.objects.bulk_update(users, ["is_beta_tester"])

        self.stdout.write(self.style.SUCCESS(f"Successfully accepted {users.count()} beta testers"))
