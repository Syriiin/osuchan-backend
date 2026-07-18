from celery import shared_task

from events.models import Event
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
