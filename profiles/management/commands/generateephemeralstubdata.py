import json
import os
import random
import time
from datetime import datetime, timezone

from django.core.management.base import BaseCommand

from common.osu.enums import Gamemode
from common.osu.utils import get_bitwise_mods, get_json_mods

from profiles.management.commands.addstubuser import (
    _generate_user,
    _merge_ephemeral_stub_data,
)
from profiles.management.commands.addstubscore import (
    _get_random_source_score,
    EPHEMERAL_DIR,
    GAMEMODE,
    MOD_COMBOS,
)

MIN_USERS = 10
SLEEP_SECONDS = 6


class Command(BaseCommand):
    help = "Generate ephemeral stub data for dev"

    def handle(self, *args, **options):
        rng = random.Random()

        self.stdout.write(f"Ensuring at least {MIN_USERS} stub users exist...")
        _ensure_users(rng)

        self.stdout.write(
            f"Looping: adding 1 score every {SLEEP_SECONDS}s ... " f"(Ctrl+C to stop)"
        )
        try:
            while True:
                user_id = rng.randint(1, MIN_USERS)
                _add_score_for_user(rng, user_id)
                time.sleep(SLEEP_SECONDS)
        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS("Stopped generator."))


def _ensure_users(rng):
    os.makedirs(EPHEMERAL_DIR, exist_ok=True)

    users_path = os.path.join(EPHEMERAL_DIR, "users.json")
    existing = {}
    if os.path.exists(users_path):
        with open(users_path) as f:
            existing = json.load(f)

    now = datetime.now(tz=timezone.utc)
    new_users = {}
    for user_id in range(1, MIN_USERS + 1):
        key = str(user_id)
        if key not in existing:
            username = f"t{user_id}"
            new_users[key] = _generate_user(rng, user_id, username, now)

    if new_users:
        with open(users_path, "w") as f:
            json.dump({**existing, **new_users}, f, indent=4)

        for key in new_users:
            _merge_ephemeral_stub_data(
                {key: {gm: [] for gm in Gamemode}}, "user_recent.json"
            )
            _merge_ephemeral_stub_data(
                {key: {gm: [] for gm in Gamemode}}, "user_best.json"
            )
            _merge_ephemeral_stub_data(
                {key: {gm: {} for gm in Gamemode}}, "scores.json"
            )

        print(f"Created {len(new_users)} new user(s)")


def _add_score_for_user(rng, user_id):
    score = _get_random_source_score()
    if score is None:
        return

    score = score.copy()
    score["date"] = datetime.now(tz=timezone.utc).isoformat()

    mod_acronyms = rng.choice(MOD_COMBOS)
    score["mods"] = get_bitwise_mods(mod_acronyms)
    score["mods_json"] = get_json_mods(
        score["mods"], add_classic=score.get("is_stable", True)
    )

    recent_path = os.path.join(EPHEMERAL_DIR, "user_recent.json")
    existing_recent = {}
    if os.path.exists(recent_path):
        with open(recent_path) as f:
            existing_recent = json.load(f)

    user_key = str(user_id)
    if user_key not in existing_recent:
        existing_recent[user_key] = {}
    if GAMEMODE not in existing_recent[user_key]:
        existing_recent[user_key][GAMEMODE] = []

    existing_recent[user_key][GAMEMODE].append(score)

    with open(recent_path, "w") as f:
        json.dump(existing_recent, f, indent=4)

    print(f"Generated new score for user ID {user_id}")
