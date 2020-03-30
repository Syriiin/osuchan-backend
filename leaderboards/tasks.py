from django.db import transaction
from celery import shared_task

from common.osu.enums import Gamemode
from common.osu import utils
from profiles.models import UserStats
from leaderboards.models import Membership

@shared_task
@transaction.atomic
def update_memberships(user_id, gamemode=Gamemode.STANDARD):
    """
    Updates all the memberships for a given user and gamemode
    """
    memberships = Membership.objects.select_related("leaderboard", "leaderboard__score_filter").filter(user_id=user_id, leaderboard__gamemode=gamemode)
    user_stats = UserStats.objects.get(user_id=user_id, gamemode=gamemode)

    for membership in memberships:
        leaderboard = membership.leaderboard
        if leaderboard.score_filter:
            scores = user_stats.scores.apply_score_filter(leaderboard.score_filter)
        else:
            scores = user_stats.scores.all()

        membership.scores.set(scores.get_score_set())
        membership.pp = utils.calculate_pp_total(score.pp for score in scores)
        membership.save()
        
    return memberships
