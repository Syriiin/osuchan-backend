import json
import os
import random
from datetime import datetime, timezone

from django.core.management.base import BaseCommand

from common.osu.enums import Gamemode

STUBDATA_DIR = os.path.join("common", "osu", "stubdata", "osuapi")
EPHEMERAL_DIR = os.path.join("common", "osu", "stubdata", "osuapi_ephemeral")

COUNTRIES = ["AU", "JP", "GB", "KR", "DE", "CA", "FR", "PL"]


class Command(BaseCommand):
    help = "Create a new user in ephemeral stub data"

    def add_arguments(self, parser):
        parser.add_argument("--seed", type=int, default=None)

    def handle(self, *args, **options):
        rng = random.Random(options["seed"])
        os.makedirs(EPHEMERAL_DIR, exist_ok=True)

        users_path = os.path.join(EPHEMERAL_DIR, "users.json")
        existing_users = {}
        if os.path.exists(users_path):
            with open(users_path) as f:
                existing_users = json.load(f)

        existing_ephemeral_ids = sorted(
            int(user_id) for user_id in existing_users.keys()
        )
        user_id = (
            (existing_ephemeral_ids[-1] + 1) if len(existing_ephemeral_ids) > 0 else 1
        )

        now = datetime.now(tz=timezone.utc)
        # short usernames based on id for easy search (s1 = stub1 ¯\_(ツ)_/¯)
        username = f"t{user_id}"
        user = _generate_user(rng, user_id, username, now)

        # add user stats
        existing_users[str(user_id)] = user
        with open(users_path, "w") as f:
            json.dump(existing_users, f, indent=4)

        # add empty recents
        _merge_ephemeral_stub_data(
            {user_id: {gamemode: [] for gamemode in Gamemode}}, "user_recent.json"
        )

        # add empty bests
        _merge_ephemeral_stub_data(
            {user_id: {gamemode: [] for gamemode in Gamemode}}, "user_best.json"
        )

        # add empty scores
        _merge_ephemeral_stub_data(
            {user_id: {gamemode: {} for gamemode in Gamemode}}, "scores.json"
        )

        self.stdout.write(
            self.style.SUCCESS(f"Created player {username} (ID {user_id})")
        )


def _merge_ephemeral_stub_data(data: dict, filename: str):
    path = os.path.join(EPHEMERAL_DIR, filename)
    existing_data = {}
    if os.path.exists(path):
        with open(path) as f:
            existing_data = json.load(f)
    with open(path, "w") as f:
        json.dump({**existing_data, **data}, f, indent=4)


def _generate_user(rng, user_id, username, now):
    return {
        gamemode: _generate_gamemode_stats(rng, user_id, username, gamemode, now)
        for gamemode in Gamemode
    }


def _generate_gamemode_stats(rng, user_id, username, gamemode, now):
    playcount = rng.randint(100, 50000)
    playtime = playcount * rng.randint(30, 120)
    ranked_score = rng.randint(1_000_000, 10_000_000_000)
    total_score = int(ranked_score * rng.uniform(3, 10))
    pp = round(rng.uniform(100, 12000), 2)
    accuracy = round(rng.uniform(85, 100), 2)
    total_hits = playcount * rng.randint(300, 700)
    acc_ratio = accuracy / 100
    count_300 = int(total_hits * (acc_ratio * 0.95 + 0.05))
    leftover = total_hits - count_300
    count_100 = int(leftover * 0.8)
    count_50 = leftover - count_100

    return {
        "user_id": user_id,
        "username": username,
        "join_date": now.isoformat(),
        "country": rng.choice(COUNTRIES),
        "playcount": playcount,
        "playtime": playtime,
        "level": round(rng.uniform(1, 101), 4),
        "ranked_score": ranked_score,
        "total_score": total_score,
        "rank": rng.randint(1, 500000),
        "country_rank": rng.randint(1, 10000),
        "pp": pp,
        "accuracy": accuracy,
        "count_300": count_300,
        "count_100": count_100,
        "count_50": count_50,
        "count_rank_ss": rng.randint(0, max(1, int(playcount * 0.0005))),
        "count_rank_ssh": rng.randint(0, max(1, int(playcount * 0.0005))),
        "count_rank_s": rng.randint(0, max(1, int(playcount * 0.005))),
        "count_rank_sh": rng.randint(0, max(1, int(playcount * 0.005))),
        "count_rank_a": rng.randint(0, max(1, int(playcount * 0.01))),
    }
