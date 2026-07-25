import json
import os
import random
from datetime import datetime, timezone

from django.core.management.base import BaseCommand, CommandError

from common.osu.utils import get_bitwise_mods, get_json_mods

STUBDATA_DIR = os.path.join("common", "osu", "stubdata", "osuapi")
EPHEMERAL_DIR = os.path.join("common", "osu", "stubdata", "osuapi_ephemeral")
GAMEMODE = "0"

MOD_COMBOS = [
    [],
    ["HD"],
    ["HR"],
    ["DT"],
    ["HD", "HR"],
    ["HD", "DT"],
    ["HR", "DT"],
    ["HD", "HR", "DT"],
    ["FL"],
    ["HD", "FL"],
    ["DT", "FL"],
    ["HR", "FL"],
    ["EZ"],
    ["EZ", "HD"],
    ["HT"],
    ["NC"],
]


class Command(BaseCommand):
    help = "Add a dev score to an existing player in ephemeral stub data"

    def add_arguments(self, parser):
        parser.add_argument("user_id", type=int)

    def handle(self, *args, **options):
        user_id = options["user_id"]

        user = _find_user(user_id)
        if user is None:
            raise CommandError(f"User {user_id} not found in stub data")
        if GAMEMODE not in user:
            raise CommandError(f"User {user_id} has no data for gamemode {GAMEMODE}")

        score = _get_random_source_score()
        if score is None:
            raise CommandError("No source scores found in stub data")

        score = score.copy()
        score["date"] = datetime.now(tz=timezone.utc).isoformat()

        mod_acronyms = random.choice(MOD_COMBOS)
        score["mods"] = get_bitwise_mods(mod_acronyms)
        score["mods_json"] = get_json_mods(
            score["mods"], add_classic=score.get("is_stable", True)
        )

        os.makedirs(EPHEMERAL_DIR, exist_ok=True)

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

        self.stdout.write(
            self.style.SUCCESS(
                f"Added 1 score for user {user_id} (gamemode {GAMEMODE})"
            )
        )


def _get_random_source_score():
    beatmap_score_lists = {}

    # build list of scores by beatmap
    path = os.path.join(STUBDATA_DIR, "scores.json")
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
        for user_scores in data.values():
            for beatmap_id, beatmap_scores in user_scores.get(GAMEMODE, {}).items():
                beatmap_score_lists.setdefault(beatmap_id, []).extend(beatmap_scores)

    for filename in ("user_best.json", "user_recent.json"):
        path = os.path.join(STUBDATA_DIR, filename)
        if not os.path.exists(path):
            continue
        with open(path) as f:
            data = json.load(f)
        for user_scores in data.values():
            for score in user_scores.get(GAMEMODE, []):
                beatmap_score_lists.setdefault(str(score["beatmap_id"]), []).append(
                    score
                )

    if len(beatmap_score_lists) == 0:
        return None

    # random beatmap, then score to not weight beatmaps with lots of score higher than others
    beatmap_id = random.choice(list(beatmap_score_lists.keys()))
    return random.choice(beatmap_score_lists[beatmap_id])


def _find_user(user_id):
    user_key = str(user_id)
    base_path = os.path.join(STUBDATA_DIR, "users.json")
    if os.path.exists(base_path):
        with open(base_path) as f:
            users = json.load(f)
        if user_key in users:
            return users[user_key]

    ephem_path = os.path.join(EPHEMERAL_DIR, "users.json")
    if os.path.exists(ephem_path):
        with open(ephem_path) as f:
            users = json.load(f)
        if user_key in users:
            return users[user_key]

    return None
