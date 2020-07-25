from django.db import transaction
from celery import shared_task

from common.osu.enums import Gamemode
from common.osu.utils import calculate_pp_total
from profiles.enums import ScoreSet, ScoreResult
from profiles.models import UserStats
from leaderboards.models import Membership

@shared_task
@transaction.atomic
def update_memberships(user_id, gamemode=Gamemode.STANDARD):
    """
    Updates all non-archived the memberships for a given user and gamemode
    """
    memberships = Membership.objects.select_related("leaderboard", "leaderboard__score_filter").filter(user_id=user_id, leaderboard__gamemode=gamemode, leaderboard__archived=False)
    user_stats = UserStats.objects.get(user_id=user_id, gamemode=gamemode)

    for membership in memberships:
        leaderboard = membership.leaderboard
        if leaderboard.score_filter:
            scores = user_stats.scores.apply_score_filter(leaderboard.score_filter)
        else:
            scores = user_stats.scores.all()

        scores = scores.get_score_set(score_set=leaderboard.score_set)
        membership.scores.set(scores)
        membership.score_count = scores.count()
        
        if leaderboard.score_set == ScoreSet.NORMAL:
            membership.pp = calculate_pp_total(score.pp for score in scores)
        elif leaderboard.score_set == ScoreSet.NEVER_CHOKE:
            membership.pp = calculate_pp_total(score.nochoke_pp if score.result & ScoreResult.CHOKE else score.pp for score in scores)
        elif leaderboard.score_set == ScoreSet.ALWAYS_FULL_COMBO:
            membership.pp = calculate_pp_total(score.nochoke_pp for score in scores)

        membership.rank = leaderboard.memberships.filter(pp__gte=membership.pp).count() + 1

        membership.save()
        
    return memberships
