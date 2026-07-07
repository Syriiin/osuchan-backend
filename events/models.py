from django.db import models

from leaderboards.models import Leaderboard
from profiles.models import OsuUser


class Event(models.Model):
    """Model representing an event"""

    id = models.BigAutoField(primary_key=True)

    slug = models.SlugField(unique=True)
    name = models.CharField()
    description = models.TextField(blank=True)
    logo = models.CharField(blank=True)
    theme_colours = models.JSONField(blank=True, default=dict)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    creation_time = models.DateTimeField()

    organisers = models.ManyToManyField(
        OsuUser, through="EventOrganiser", related_name="organised_events"
    )
    attendees = models.ManyToManyField(
        OsuUser, through="EventAttendee", related_name="events"
    )

    def is_organiser(self, osu_user_id: int) -> bool:
        return self.organisers.filter(id=osu_user_id).exists()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(start_date__lt=models.F("end_date")),
                name="event_start_before_end",
            )
        ]


class EventOrganiser(models.Model):
    """Through model linking an organiser user to an event"""

    id = models.BigAutoField(primary_key=True)
    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="event_organisers"
    )
    user = models.ForeignKey(
        OsuUser, on_delete=models.CASCADE, related_name="event_organisers"
    )

    def __str__(self):
        return f"[{self.event.name}] {self.user.username}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["event", "user"], name="unique_event_organiser"
            )
        ]


class EventAttendee(models.Model):
    """Through model linking an attendee user to an event"""

    id = models.BigAutoField(primary_key=True)
    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="event_attendees"
    )
    user = models.ForeignKey(
        OsuUser, on_delete=models.CASCADE, related_name="event_attendees"
    )

    def __str__(self):
        return f"[{self.event.name}] {self.user.username}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["event", "user"], name="unique_event_attendee"
            )
        ]


class EventLeaderboard(models.Model):
    """Through model linking a leaderboard to an event"""

    id = models.BigAutoField(primary_key=True)
    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="event_leaderboards"
    )
    leaderboard = models.OneToOneField(
        Leaderboard,
        on_delete=models.CASCADE,
        related_name="event_leaderboard",
    )

    def __str__(self):
        return f"{self.event.name}: {self.leaderboard.name}"
