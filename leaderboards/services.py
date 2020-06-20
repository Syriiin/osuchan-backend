from django.db import transaction

from leaderboards.models import Leaderboard
from leaderboards.enums import LeaderboardAccessType

@transaction.atomic
def create_leaderboard(owner_id, leaderboard):
    """
    Create a personal leaderboard for a passed owner_id from an unsaved Leaderboard instance
    """
    # Set relations and update membership
    leaderboard.owner_id = owner_id
    leaderboard.member_count = 1
    leaderboard.save()
    leaderboard.update_membership(owner_id)
    return leaderboard

@transaction.atomic
def create_membership(leaderboard_id, user_id):
    leaderboard = Leaderboard.objects.get(id=leaderboard_id)
    membership = leaderboard.update_membership(user_id)
    leaderboard.update_member_count()
    return membership

@transaction.atomic
def delete_membership(leaderboard_id, user_id):
    """
    Delete a membership and update Leaderboard.member_count
    """
    leaderboard = Leaderboard.objects.exclude(access_type=LeaderboardAccessType.GLOBAL).get(id=leaderboard_id)
    membership = leaderboard.members.get(user_id=user_id)
    membership.delete()
    leaderboard.update_member_count()
    return True
