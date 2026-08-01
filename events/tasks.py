from datetime import datetime, timedelta, timezone

from celery import shared_task

from common.osu.enums import Gamemode
from events.models import Event
from events.services import (
    recalculate_event_stats,
    update_attendee_challenge_scores,
)
from leaderboards.services import update_membership
from profiles.models import UserStats


@shared_task
def refresh_event_leaderboards(event_id: int) -> None:
    """Re-evaluate memberships for all attendees on all of an event's leaderboards."""
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        return

    user_ids = list(event.event_attendees.values_list("user_id", flat=True))
    for event_leaderboard in event.event_leaderboards.select_related("leaderboard"):
        for user_id in user_ids:
            update_membership(
                event_leaderboard.leaderboard, user_id, skip_notifications=True
            )


@shared_task(priority=6)
def update_event_stats(event_id: int) -> None:
    """Recalculate stats for a single event."""
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        return

    recalculate_event_stats(event)


@shared_task(priority=7)
def dispatch_update_all_current_event_stats():
    """Dispatch stat recalculation for all currently-running events."""
    now = datetime.now(tz=timezone.utc)
    current_events = Event.objects.filter(
        start_date__lte=now,
        end_date__gte=now,
    )

    for event in current_events:
        update_event_stats.delay(event_id=event.id)


@shared_task
def update_user_event_challenge_scores(user_id: int) -> None:
    """Update beatmap challenge scores for a given user on all current event beatmap challenges"""
    now = datetime.now(tz=timezone.utc)
    current_events = Event.objects.filter(
        attendees__id=user_id,
        start_date__lte=now,
        end_date__gte=now,
    )

    for event in current_events:
        for challenge in event.beatmap_challenges.all():
            update_attendee_challenge_scores(challenge, user_id)


@shared_task(priority=7)
def dispatch_update_all_current_event_attendees():
    # TODO: fix circular dependency
    from profiles.tasks import update_user_recent

    now = datetime.now(tz=timezone.utc)
    current_events = Event.objects.filter(
        start_date__lte=now,
        end_date__gte=now,
    )

    for event in current_events:
        for attendee in event.attendees.all():
            for gamemode in Gamemode:
                update_user_recent.apply_async(
                    kwargs={
                        "user_id": attendee.id,
                        "gamemode": gamemode,
                    },
                    priority=6,
                )


@shared_task(priority=7)
def dispatch_update_all_current_event_active_attendees():
    # TODO: fix circular dependency
    from profiles.tasks import update_user_recent

    now = datetime.now(tz=timezone.utc)
    current_events = Event.objects.filter(
        start_date__lte=now,
        end_date__gte=now,
    )

    for event in current_events:
        active_attendees_stats = UserStats.objects.filter(
            user_id__in=event.attendees.values_list("id"),
            scores__date__gte=datetime.now(tz=timezone.utc) - timedelta(minutes=30),
        ).distinct()
        for user_stats in active_attendees_stats:
            update_user_recent.apply_async(
                kwargs={
                    "user_id": user_stats.user_id,
                    "gamemode": user_stats.gamemode,
                },
                priority=6,
            )
