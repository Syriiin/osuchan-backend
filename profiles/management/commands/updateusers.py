import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from profiles.services import fetch_user


class Command(BaseCommand):
    help = "Runs user update for given users"

    def add_arguments(self, parser):
        parser.add_argument("gamemode", nargs=1, type=int)
        parser.add_argument("user_ids", nargs="*", type=int)
        parser.add_argument("--file")

    def handle(self, *args, **options):
        gamemode = options["gamemode"][0]

        user_ids = options["user_ids"]

        if options["file"]:
            file_path = os.path.join(settings.BASE_DIR, options["file"])
            with open(file_path, "r") as fp:
                user_ids += fp.readlines()

        for user_id in user_ids:
            user_stats = fetch_user(user_id=user_id, gamemode=gamemode)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully updated user {user_stats.user.username} ({user_stats.user_id})"
                )
            )
