import json
import os
import urllib.request

from django.conf import settings
from django.core.management.base import BaseCommand
from tqdm import tqdm

from common.osu.enums import Gamemode
from common.osu.osuapi import LiveOsuApiV2

API_STUBDATA_DIR = "common/osu/stubdata/osuapi"
BEATMAP_STUBDATA_DIR = "common/osu/stubdata/beatmap_provider"

USER_IDS = [
    5701575,  # syrin
    6566698,  # nayrus
    7562902,  # mrekk
]

BEATMAP_IDS_FOR_SCORES = [
    362949,
]


class Command(BaseCommand):
    help = "Generates stub data for common.osu.osuapi"

    def handle(self, *args, **options):
        api = LiveOsuApiV2()

        self.stdout.write("Generating stub data for osuapi")

        self.stdout.write("Fetching users")
        users = {}
        for user_id in tqdm(USER_IDS, desc="Users"):
            users[str(user_id)] = {}
            for gamemode in tqdm(Gamemode, desc="Gamemodes", leave=False):
                user_data = api.get_user_by_id(user_id, gamemode)
                if user_data is None:
                    raise Exception(f"User {user_id} not found")
                users[str(user_id)][str(gamemode.value)] = user_data.as_json()
        with open(os.path.join(API_STUBDATA_DIR, "users_v2.json"), "w") as fp:
            json.dump(users, fp, indent=4)

        self.stdout.write("Fetching user bests")
        user_bests = {
            str(user_id): {
                str(gamemode.value): [
                    score.as_json()
                    for score in api.get_user_best_scores(user_id, gamemode)[:5]
                ]
                for gamemode in tqdm(Gamemode, desc="Gamemodes", leave=False)
            }
            for user_id in tqdm(USER_IDS, desc="Users")
        }
        with open(os.path.join(API_STUBDATA_DIR, "user_best_v2.json"), "w") as fp:
            json.dump(user_bests, fp, indent=4)

        self.stdout.write("Fetching user recents")
        user_recents = {
            str(user_id): {
                str(gamemode.value): [
                    score.as_json()
                    for score in api.get_user_recent_scores(user_id, gamemode)[:5]
                ]
                for gamemode in tqdm(Gamemode, desc="Gamemodes", leave=False)
            }
            for user_id in tqdm(USER_IDS, desc="Users")
        }
        with open(os.path.join(API_STUBDATA_DIR, "user_recent_v2.json"), "w") as fp:
            json.dump(user_recents, fp, indent=4)

        self.stdout.write("Fetching scores")
        scores = {
            str(user_id): {
                str(gamemode): {
                    str(beatmap_id): [
                        score.as_json()
                        for score in api.get_user_scores_for_beatmap(
                            beatmap_id, user_id, gamemode
                        )
                    ]
                    for beatmap_id in tqdm(
                        BEATMAP_IDS_FOR_SCORES, desc="Beatmaps", leave=False
                    )
                }
                for gamemode in tqdm(Gamemode, desc="Gamemodes", leave=False)
            }
            for user_id in tqdm(USER_IDS, desc="Users")
        }
        with open(os.path.join(API_STUBDATA_DIR, "scores_v2.json"), "w") as fp:
            json.dump(scores, fp, indent=4)

        beatmap_ids = []
        for user in user_bests:
            for gamemode in user_bests[user]:
                for score in user_bests[user][gamemode]:
                    beatmap_ids.append(score["beatmap_id"])

        for user in user_recents:
            for gamemode in user_recents[user]:
                for score in user_recents[user][gamemode]:
                    beatmap_ids.append(score["beatmap_id"])

        for user in scores:
            for gamemode in scores[user]:
                for beatmap_id in scores[user][gamemode]:
                    beatmap_ids.append(int(beatmap_id))

        beatmap_ids = sorted(set(beatmap_ids))

        self.stdout.write("Fetching beatmaps")
        beatmaps = {}
        for beatmap_id in tqdm(beatmap_ids, desc="Beatmaps"):
            beatmap_data = api.get_beatmap(beatmap_id)
            if beatmap_data is None:
                raise Exception(f"Beatmap {beatmap_id} not found")
            beatmaps[str(beatmap_id)] = beatmap_data.as_json()

        with open(os.path.join(API_STUBDATA_DIR, "beatmaps_v2.json"), "w") as fp:
            json.dump(beatmaps, fp, indent=4)

        self.stdout.write("Downloading beatmap files")
        for beatmap_id in tqdm(beatmap_ids, desc="Beatmaps"):
            beatmap_path = os.path.join(BEATMAP_STUBDATA_DIR, f"{beatmap_id}.osu")
            if not os.path.isfile(beatmap_path):
                beatmap_url = f"{settings.BEATMAP_DL_URL}{beatmap_id}"
                urllib.request.urlretrieve(beatmap_url, beatmap_path)
                if os.path.getsize(beatmap_path) == 0:
                    os.remove(beatmap_path)
                    raise Exception(f"Beatmap {beatmap_id} not found at {beatmap_url}")
