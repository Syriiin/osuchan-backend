from django.db import transaction
from celery import shared_task

from datetime import datetime, timedelta

import pytz

from common.osu import apiv1
from common.osu.enums import Gamemode
from profiles.models import OsuUser, UserStats
from leaderboards.models import Leaderboard, Membership
from leaderboards.enums import LeaderboardAccessType
from leaderboards.tasks import update_memberships

@shared_task
@transaction.atomic
def update_user(user_id=None, username=None, gamemode=Gamemode.STANDARD):
    """
    Fetch and add user with top 100 scores
    """
    # Check for invalid inputs
    if not user_id and not username:
        raise ValueError("Must pass either username or user_id")

    # Fetch user data from osu api
    if user_id:
        user_data = apiv1.get_user(user_id, user_id_type="id", gamemode=gamemode)
    else:
        user_data = apiv1.get_user(username, user_id_type="string", gamemode=gamemode)

    # Check for response
    if not user_data:
        if user_id:
            # User either doesnt exist, or is restricted and needs to be disabled
            try:
                osu_user = OsuUser.objects.select_for_update().get(id=user_id)
                # Restricted
                osu_user.disabled = True
                osu_user.save()
            except OsuUser.DoesNotExist:
                # Doesnt exist (or was restricted before osuchan ever saw them)
                pass
            return None
        else:
            # User either doesnt exist, is restricted, or name changed
            try:
                osu_user = OsuUser.objects.select_for_update().get(username=username)
                # Fetch from osu api with user id incase of name change
                user_data = apiv1.get_user(osu_user.id, user_id_type="id", gamemode=gamemode)

                if not user_data:
                    # Restricted
                    osu_user.disabled = True
                    osu_user.save()
                    return None
            except OsuUser.DoesNotExist:
                # Doesnt exist
                return None

    # Get or create UserStats model
    try:
        user_stats = UserStats.objects.select_for_update().select_related("user").get(user_id=user_data["user_id"], gamemode=gamemode)
        
        # Check if user was updated recently (update enqueued multiple times before processing)
        if user_stats.last_updated > (datetime.utcnow().replace(tzinfo=pytz.UTC) - timedelta(minutes=5)):
            return user_stats

        osu_user = user_stats.user
    except UserStats.DoesNotExist:
        user_stats = UserStats()
        user_stats.gamemode = gamemode

        # Get or create OsuUser model
        try:
            osu_user = OsuUser.objects.select_for_update().get(id=user_data["user_id"])
        except OsuUser.DoesNotExist:
            osu_user = OsuUser(id=user_data["user_id"])

            # Create memberships with global leaderboards
            global_leaderboards = Leaderboard.objects.filter(access_type=LeaderboardAccessType.GLOBAL).values("id")
            # TODO: refactor this to be somewhere else. dont really like setting pp to 0
            global_memberships = [Membership(leaderboard_id=leaderboard["id"], user_id=osu_user.id, pp=0) for leaderboard in global_leaderboards]
            Membership.objects.bulk_create(global_memberships)

    # Update OsuUser fields
    osu_user.username = user_data["username"]
    osu_user.country = user_data["country"]
    osu_user.join_date = datetime.strptime(user_data["join_date"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.UTC)
    osu_user.disabled = False

    # Save OsuUser model
    osu_user.save()

    # Set OsuUser relation id on UserStats
    user_stats.user_id = int(osu_user.id)

    # Update UserStats fields
    user_stats.playcount = int(user_data["playcount"]) if user_data["playcount"] is not None else 0
    user_stats.playtime = int(user_data["total_seconds_played"]) if user_data["total_seconds_played"] is not None else 0
    user_stats.level = float(user_data["level"]) if user_data["level"] is not None else 0
    user_stats.ranked_score = int(user_data["ranked_score"]) if user_data["ranked_score"] is not None else 0
    user_stats.total_score = int(user_data["total_score"]) if user_data["total_score"] is not None else 0
    user_stats.rank = int(user_data["pp_rank"]) if user_data["pp_rank"] is not None else 0
    user_stats.country_rank = int(user_data["pp_country_rank"]) if user_data["pp_country_rank"] is not None else 0
    user_stats.pp = float(user_data["pp_raw"]) if user_data["pp_raw"] is not None else 0
    user_stats.accuracy = float(user_data["accuracy"]) if user_data["accuracy"] is not None else 0
    user_stats.count_300 = int(user_data["count300"]) if user_data["count300"] is not None else 0
    user_stats.count_100 = int(user_data["count100"]) if user_data["count100"] is not None else 0
    user_stats.count_50 = int(user_data["count50"]) if user_data["count50"] is not None else 0
    user_stats.count_rank_ss = int(user_data["count_rank_ss"]) if user_data["count_rank_ss"] is not None else 0
    user_stats.count_rank_ssh = int(user_data["count_rank_ssh"]) if user_data["count_rank_ssh"] is not None else 0
    user_stats.count_rank_s = int(user_data["count_rank_s"]) if user_data["count_rank_s"] is not None else 0
    user_stats.count_rank_sh = int(user_data["count_rank_sh"]) if user_data["count_rank_sh"] is not None else 0
    user_stats.count_rank_a = int(user_data["count_rank_a"]) if user_data["count_rank_a"] is not None else 0

    # Fetch user scores from osu api
    score_data_list = []
    score_data_list.extend(apiv1.get_user_best(user_stats.user_id, gamemode=gamemode, limit=100))
    if gamemode == Gamemode.STANDARD:
        # If standard, check user recent because we will be able to calculate pp for those scores
        score_data_list.extend(score for score in apiv1.get_user_recent(user_stats.user_id, gamemode=gamemode, limit=50) if score["rank"] != "F")
    
    # Process and add scores
    user_stats.add_scores_from_data(score_data_list)

    # Update memberships
    update_memberships.delay(user_id=user_stats.user_id, gamemode=user_stats.gamemode)

    return user_stats
