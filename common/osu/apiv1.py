from django.conf import settings

import requests

api_key = settings.OSU_API_V1_KEY
base_url = settings.OSU_API_V1_BASE_URL

def get_legacy_endpoint(endpoint_name, **kwargs):
    # Remove any None arguments passed in kwargs
    payload = {k: v for k, v in kwargs.items() if v}

    # Add api key to payload
    payload["k"] = api_key

    # Return result of GET request
    return requests.get(base_url + endpoint_name, params=payload).json()

# API v1 endpoints
# https://github.com/ppy/osu-api/wiki

# Beatmap
def get_beatmaps(
    beatmap_id=None,
    beatmap_set_id=None,
    user_id=None,
    user_id_type="id",
    gamemode=None,
    include_converted=None,
    since=None,
    beatmap_hash=None,
    limit=None
):
    return get_legacy_endpoint("get_beatmaps",
        b=beatmap_id,
        s=beatmap_set_id,
        u=user_id,
        type=user_id_type,
        m=gamemode,
        a=include_converted,
        since=since,
        h=beatmap_hash,
        limit=limit
    )

# User
def get_user(
    user_id,
    user_id_type="id",
    gamemode=None,
    event_days=None
):
    return get_legacy_endpoint("get_user",
        u=user_id,
        type=user_id_type,
        m=gamemode,
        event_days=event_days
    )[0]

# Scores
def get_scores(
    beatmap_id,
    user_id=None,
    user_id_type="id",
    gamemode=None,
    mods=None,
    limit=None
):
    return get_legacy_endpoint("get_scores",
        b=beatmap_id,
        u=user_id,
        type=user_id_type,
        m=gamemode,
        mods=mods,
        limit=limit
    )

# Best Performances
def get_user_best(
    user_id,
    user_id_type="id",
    gamemode=None,
    limit=None
):
    return get_legacy_endpoint("get_user_best",
        u=user_id,
        type=user_id_type,
        m=gamemode,
        limit=limit
    )

# Recently Played
def get_user_recent(
    user_id,
    user_id_type="id",
    gamemode=None,
    limit=None
):
    return get_legacy_endpoint("get_user_recent",
        u=user_id,
        type=user_id_type,
        m=gamemode,
        limit=limit
    )

# Multiplayer
def get_match(
    match_id
):
    return get_legacy_endpoint("get_match",
        mp=match_id
    )

# Get replay data
def get_replay(
    beatmap_id,
    user_id,
    gamemode,
    mods=None
):
    return get_legacy_endpoint("get_replay",
        b=beatmap_id,
        u=user_id,
        m=gamemode,
        mods=mods
    )
