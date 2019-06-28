from django.db import transaction

from leaderboards.models import Leaderboard

@transaction.atomic
def create_leaderboard(owner_id, leaderboard):
    """
    Create a personal leaderboard for a passed owner_id from an unsaved Leaderboard instance
    """
    # Set relations and update membership
    leaderboard.owner_id = owner_id
    leaderboard.save()
    leaderboard.update_membership(owner_id)
    return leaderboard

@transaction.atomic
def create_membership(leaderboard_id, user_id):
    leaderboard = Leaderboard.objects.get(id=leaderboard_id)
    membership = leaderboard.update_membership(user_id)
    return membership