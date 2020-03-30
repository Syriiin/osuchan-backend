from django.conf import settings

import os
import urllib.request

beatmap_cache_path = settings.BEATMAP_CACHE_PATH
beatmap_dl_url = settings.BEATMAP_DL_URL

def get_beatmap_path(beatmap_id):
    # get beatmap path
    beatmap_id = str(beatmap_id)
    beatmap_path = os.path.join(beatmap_cache_path, beatmap_id)

    # download beatmap if we dont have it
    if not os.path.isfile(beatmap_path):
        bm_url = beatmap_dl_url + beatmap_id
        urllib.request.urlretrieve(bm_url, beatmap_path)

    return beatmap_path

def parse_int_or_none(input):
    try:
        return int(input)
    except (ValueError, TypeError):
        return None
    