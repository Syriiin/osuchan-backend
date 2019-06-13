from django.db import transaction

from datetime import datetime, timedelta
import pytz

from common.osu import apiv1
from common.osu.enums import Gamemode
from profiles.models import OsuUser, UserStats

# COMMAND: UPDATE PROFILE
@transaction.atomic
def fetch_user(user_id=None, username=None, gamemode=Gamemode.STANDARD):
    """
    Fetch and add user with top 100 scores (updates max once each 5 minutes)
    """
    # Check for invalid inputs
    if not user_id and not username:
        raise ValueError("Must pass either username or user_id")

    # Get or create UserStats model
    try:
        if user_id:
            user_stats = UserStats.objects.select_for_update().get(user_id=user_id, gamemode=gamemode)
        else:
            user_stats = UserStats.objects.select_for_update().get(user__username__iexact=username, gamemode=gamemode)
        
        # Return without updating if the user was updated less than 5 minutes ago
        if user_stats.last_updated > (datetime.utcnow().replace(tzinfo=pytz.UTC) - timedelta(minutes=5)):
            return user_stats
    except UserStats.DoesNotExist:
        user_stats = UserStats()
        user_stats.gamemode = gamemode

    # Fetch user data from osu api
    if user_id:
        user_data = apiv1.get_user(user_id, user_id_type="id", gamemode=gamemode)
    else:
        user_data = apiv1.get_user(username, user_id_type="string", gamemode=gamemode)

    # Check for response
    if not user_data:
        # user either doesnt exist, or is restricted
        # TODO: somehow determine if user was restricted and set their OsuUser to disabled
        return None  # TODO: replace these type of "return None"s with exception raising

    # Get or create OsuUser model
    try:
        osu_user = OsuUser.objects.select_for_update().get(id=user_data["user_id"])
    except OsuUser.DoesNotExist:
        osu_user = OsuUser(id=user_data["user_id"])

    # Update OsuUser fields
    osu_user.username = user_data["username"]
    osu_user.country = user_data["country"]
    osu_user.join_date = datetime.strptime(user_data["join_date"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.UTC)
    osu_user.disabled = False

    # Save OsuUser model
    osu_user.save()

    # Set OsuUser relation id on UserStats
    user_stats.user_id = int(user_data["user_id"])

    # Update UserStats fields
    user_stats.playcount = int(user_data["playcount"])
    user_stats.playtime = int(user_data["total_seconds_played"])
    user_stats.level = float(user_data["level"])
    user_stats.ranked_score = int(user_data["ranked_score"])
    user_stats.total_score = int(user_data["total_score"])
    user_stats.rank = int(user_data["pp_rank"])
    user_stats.country_rank = int(user_data["pp_country_rank"])
    user_stats.pp = float(user_data["pp_raw"])
    user_stats.accuracy = float(user_data["accuracy"])
    user_stats.count_300 = int(user_data["count300"])
    user_stats.count_100 = int(user_data["count100"])
    user_stats.count_50 = int(user_data["count50"])
    user_stats.count_rank_ss = int(user_data["count_rank_ss"])
    user_stats.count_rank_ssh = int(user_data["count_rank_ssh"])
    user_stats.count_rank_s = int(user_data["count_rank_s"])
    user_stats.count_rank_sh = int(user_data["count_rank_sh"])
    user_stats.count_rank_a = int(user_data["count_rank_a"])

    # Fetch user scores from osu api
    score_data_list = apiv1.get_user_best(user_stats.user_id, gamemode=gamemode, limit=100)
    
    # Process and add scores
    user_stats.add_scores_from_data(score_data_list)

    return user_stats

@transaction.atomic
def fetch_scores(user_id, beatmap_id, gamemode):
    """
    Fetch and add scores for a user on a beatmap in a gamemode
    """
    # Fetch UserStats from database
    user_stats = UserStats.objects.select_for_update().get(user_id=user_id, gamemode=gamemode)
    
    # Fetch score data from osu api
    score_data_list = apiv1.get_scores(beatmap_id=beatmap_id, user_id=user_id, gamemode=gamemode)

    # Process add scores
    unchanged_scores, updated_scores, new_scores = user_stats.add_scores_from_data(score_data_list, override_beatmap_id=beatmap_id)

    return [*unchanged_scores, *updated_scores, *new_scores]
