from django.db import transaction
from rest_framework.exceptions import PermissionDenied

from common.osu.utils import calculate_pp_total
from leaderboards.enums import LeaderboardAccessType
from leaderboards.models import Leaderboard, Membership, MembershipScore
from profiles.models import OsuUser, Score


@transaction.atomic
def create_leaderboard(owner_id, leaderboard):
    """
    Create a personal leaderboard for a passed owner_id from an unsaved Leaderboard instance
    """
    # Set relations and update membership
    leaderboard.owner_id = owner_id
    leaderboard.member_count = 1
    leaderboard.score_filter.save()
    leaderboard.save()
    update_membership(leaderboard, owner_id)
    return leaderboard


@transaction.atomic
def create_membership(leaderboard_id, user_id):
    """
    Creates a membership with a community leaderboard and update Leaderboard.member_count
    """
    leaderboard = Leaderboard.community_leaderboards.get(id=leaderboard_id)
    membership = update_membership(leaderboard, user_id)
    leaderboard.update_member_count()
    return membership


@transaction.atomic
def delete_membership(membership):
    """
    Delete a membership of a leaderboard and update Leaderboard.member_count
    """
    membership.delete()
    membership.leaderboard.update_member_count()
    return True


@transaction.atomic
def update_membership(leaderboard: Leaderboard, user_id: int):
    """
    Creates or updates a membership for a given user on a given leaderboard
    """
    try:
        membership = leaderboard.memberships.select_for_update().get(user_id=user_id)
    except Membership.DoesNotExist:
        if (
            leaderboard.access_type
            in (
                LeaderboardAccessType.PUBLIC_INVITE_ONLY,
                LeaderboardAccessType.PRIVATE,
            )
            and leaderboard.owner_id != user_id
        ):
            # Check if user has been invited
            try:
                invitees = leaderboard.invitees.filter(id=user_id)
            except OsuUser.DoesNotExist:
                raise PermissionDenied("You must be invited to join this leaderboard.")

            # Invite is being accepted
            leaderboard.invitees.remove(*invitees)

        # Create new membership
        membership = Membership.objects.create(
            user_id=user_id,
            leaderboard=leaderboard,
            pp=0,
            score_count=0,
            rank=leaderboard.member_count + 1,
        )

    # Get leaderboard records before updating, so we can compare
    pp_record = leaderboard.get_pp_record()
    leaderboard_top_player = leaderboard.get_top_membership()

    scores = Score.objects.filter(
        user_stats__user_id=user_id, user_stats__gamemode=leaderboard.gamemode
    )

    if not leaderboard.allow_past_scores:
        scores = scores.filter(date__gte=membership.join_date)

    if leaderboard.score_filter:
        scores = scores.apply_score_filter(leaderboard.score_filter)

    scores = scores.get_score_set(leaderboard.gamemode, score_set=leaderboard.score_set)

    membership_scores = [
        MembershipScore(
            membership=membership,
            leaderboard=leaderboard,
            score=score,
            performance_total=score.default_performance_total,
        )
        for score in scores
        # Skip scores missing performance calculation
        if score.default_performance_total is not None
    ]

    MembershipScore.objects.bulk_create(
        membership_scores,
        update_conflicts=True,
        update_fields=["performance_total"],
        unique_fields=["membership_id", "score_id"],
    )

    outdated_membershipscores = MembershipScore.objects.filter(
        membership=membership
    ).exclude(score_id__in=[score.id for score in scores])
    outdated_membershipscores.delete()

    membership.score_count = len(membership_scores)

    membership.pp = calculate_pp_total(
        score.performance_total for score in membership_scores
    )

    membership.rank = leaderboard.memberships.filter(pp__gt=membership.pp).count() + 1

    membership.save()

    if leaderboard.notification_discord_webhook_url != "":
        # Check for new top score
        if (
            len(membership_scores) > 0
            and membership_scores[0].performance_total > pp_record
        ):
            # NOTE: need to use a function with default params here so the closure has the correct variables
            def send_notification(
                leaderboard_id=leaderboard.id,
                score_id=membership_scores[0].score_id,
            ):
                from leaderboards.tasks import send_leaderboard_top_score_notification

                send_leaderboard_top_score_notification.delay(leaderboard_id, score_id)

            transaction.on_commit(send_notification)

        # Check for new top player
        if (
            leaderboard_top_player is not None
            and leaderboard_top_player.user_id != membership.user_id
            and membership.rank == 1
            and membership.pp > 0
        ):
            # NOTE: need to use a function with default params here so the closure has the correct variables
            def send_notification(
                leaderboard_id=leaderboard.id,
                user_id=membership.user_id,
            ):
                from leaderboards.tasks import send_leaderboard_top_player_notification

                send_leaderboard_top_player_notification.delay(leaderboard_id, user_id)

            transaction.on_commit(send_notification)

    return membership
