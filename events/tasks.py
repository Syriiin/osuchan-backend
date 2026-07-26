from datetime import datetime, timezone

from celery import shared_task

from events.models import Event
from events.services import update_attendee_challenge_scores
from leaderboards.services import update_membership


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
