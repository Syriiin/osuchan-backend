from django.db import transaction
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

import os

from osuauth.models import User

class Command(BaseCommand):
    help = "Refreshes the specified global leaderboards for all users"

    def add_arguments(self, parser):
        parser.add_argument("accept_count", nargs=1, type=int)
        parser.add_argument("accept_type", nargs=1, type=str)
        parser.add_argument("--file")

    def handle(self, *args, **options):
        accept_count = options["accept_count"][0]
        accept_type = options["accept_type"][0]

        users = User.objects.filter(is_beta_tester=False)

        if accept_type == "random":
            users = users.order_by("?")
        else:
            users = users.order_by("date_joined")

        if options["file"]:
            file_path = os.path.join(settings.BASE_DIR, options["file"])
            with open(file_path, "r") as fp:
                users = users.filter(osu_user_id__in=[int(user_id.replace("\n", "")) for user_id in fp.readlines()])

        users = users[:accept_count]

        for user in users:
            user.is_beta_tester = True

        User.objects.bulk_update(users, ["is_beta_tester"])

        self.stdout.write(self.style.SUCCESS(f"Successfully accepted {users.count()} beta testers"))
