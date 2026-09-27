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
    try:
        membership = leaderboard.memberships.get(user_id=user_id)
    except Membership.DoesNotExist:
        membership = update_membership(leaderboard, user_id)
        leaderboard.update_member_count()
    return membership


@transaction.atomic
def delete_membership(membership):
    """
    Delete a membership of a leaderboard and update Leaderboard.member_count
    """
    leaderboard_id = membership.leaderboard_id
    user_id = membership.user_id
    membership.delete()
    membership.leaderboard.update_member_count()
    prune_member_top_scores(leaderboard_id, user_id)
    return True


@transaction.atomic
def update_leaderboard_top_scores(
    leaderboard: Leaderboard, member_scores: list[Score], user_id: int
):
    """
    Merge a member's scores into the leaderboard's stored top-100 list, removing any missing scores from the member.
    """
    # lock leaderboard while top scores are being updated
    locked_leaderboard = Leaderboard.objects.select_for_update().get(id=leaderboard.id)

    member_scores_data = [
        {"score_id": score.id, "value": score.performance_total, "user_id": user_id}
        for score in member_scores
    ]

    top_member_scores = sorted(
        member_scores_data,
        key=lambda score: score.get("value"),
        reverse=True,
    )[:100]

    leaderboard_top_scores_without_member = [
        score for score in locked_leaderboard.top_scores if score["user_id"] != user_id
    ]

    merged_top_scores = leaderboard_top_scores_without_member + top_member_scores

    new_top_scores = [
        score
        for score in sorted(
            merged_top_scores, key=lambda score: score.get("value"), reverse=True
        )[:100]
    ]

    if new_top_scores != locked_leaderboard.top_scores:
        locked_leaderboard.top_scores = new_top_scores
        locked_leaderboard.save(update_fields=["top_scores"])

    leaderboard.top_scores = new_top_scores


@transaction.atomic
def prune_member_top_scores(leaderboard_id: int, user_id: int):
    """
    Prune a member's scores from the Leaderboard.top_scores list.
    Necessary when a member is deleted.
    """
    # note, this function has the unfortunate side effect that the leaderboard top scores list will be an incomplete top 100 if any scores are actually removed
    # querying to rebuild the full top score list from scratch is too slow for large leaderboards, but maybe theres a middleground
    # TODO: consider how we can fix this. perhaps by storing a top performance value per member so we can build the list without without querying all members?
    locked_leaderboard = Leaderboard.objects.select_for_update().get(id=leaderboard_id)
    new_top_scores = [
        top_score
        for top_score in locked_leaderboard.top_scores
        if top_score.get("user_id") != user_id
    ]

    if new_top_scores != locked_leaderboard.top_scores:
        locked_leaderboard.top_scores = new_top_scores
        locked_leaderboard.save(update_fields=["top_scores"])


@transaction.atomic
def update_membership(
    leaderboard: Leaderboard, user_id: int, skip_notifications: bool = False
):
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

    if not skip_notifications and leaderboard.notification_discord_webhook_url != "":
        # Get leaderboard records before updating, so we can compare for notifications
        pp_record = leaderboard.get_pp_record()
        leaderboard_top_player = leaderboard.get_top_membership()
        old_member_pp_record = membership.get_pp_record()
        old_score_count = membership.score_count
        old_top_10_scores = set(leaderboard.get_top_scores(limit=10))

    scores = Score.objects.filter(
        user_stats__user_id=user_id, user_stats__gamemode=leaderboard.gamemode
    )

    if not leaderboard.allow_past_scores:
        scores = scores.filter(date__gte=membership.join_date)

    if leaderboard.score_filter:
        scores = scores.apply_score_filter(leaderboard.score_filter)

    scores = scores.get_score_set(
        leaderboard.gamemode,
        score_set=leaderboard.score_set,
        calculator_engine=leaderboard.calculator_engine,
        primary_performance_value=leaderboard.primary_performance_value,
    )

    # Skip scores missing performance calculation
    valid_scores = [score for score in scores if score.performance_total is not None]

    membership_scores = [
        MembershipScore(
            membership=membership,
            leaderboard=leaderboard,
            score=score,
            performance_total=score.performance_total,
        )
        for score in valid_scores
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

    update_leaderboard_top_scores(leaderboard, valid_scores, user_id)

    if not skip_notifications and leaderboard.notification_discord_webhook_url != "":
        notification_settings = leaderboard.notification_settings

        # Check for new top score
        if (
            notification_settings.get("top_score")
            and len(membership_scores) > 0
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
            notification_settings.get("top_player")
            and leaderboard_top_player is not None
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

        # Check for first score on leaderboard
        if (
            notification_settings.get("player_first_score")
            and old_score_count == 0
            and membership.score_count > 0
        ):

            def send_notification(
                leaderboard_id=leaderboard.id,
                score_id=membership.scores.order_by("date").first().id,
            ):
                from leaderboards.tasks import (
                    send_leaderboard_player_first_score_notification,
                )

                send_leaderboard_player_first_score_notification.delay(
                    leaderboard_id, score_id
                )

            transaction.on_commit(send_notification)

        personal_pp_record_score = (
            membership_scores[0] if len(membership_scores) > 0 else None
        )
        personal_pp_record = (
            personal_pp_record_score.performance_total
            if personal_pp_record_score is not None
            else 0
        )

        # Check for personal pp record improvement
        if (
            notification_settings.get("player_top_score")
            and personal_pp_record > old_member_pp_record
        ):

            def send_notification(
                leaderboard_id=leaderboard.id,
                user_id=membership.user_id,
            ):
                from leaderboards.tasks import (
                    send_leaderboard_player_top_score_notification,
                )

                send_leaderboard_player_top_score_notification.delay(
                    leaderboard_id, user_id, personal_pp_record_score.score_id
                )

            transaction.on_commit(send_notification)

        # Check for top 10 scores (excluding #1 since it has it's own notification)
        if notification_settings.get("top_10_score") and len(membership_scores) > 0:
            leaderboard_top_10_scores = leaderboard.get_top_scores(limit=10)[
                1:
            ]  # Exclude top score since it has it's own notification

            for rank, score in enumerate(leaderboard_top_10_scores, start=2):
                if score not in old_top_10_scores:

                    def send_notification(
                        leaderboard_id=leaderboard.id,
                        score_id=score.id,
                        rank=rank,
                    ):
                        from leaderboards.tasks import (
                            send_leaderboard_top_10_score_notification,
                        )

                        send_leaderboard_top_10_score_notification.delay(
                            leaderboard_id, score_id, rank
                        )

                    transaction.on_commit(send_notification)

    return membership
