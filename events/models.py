from django.db import models

from events.enums import BeatmapChallengeType
from leaderboards.models import Leaderboard
from profiles.enums import ScoreMutation
from profiles.models import Beatmap, OsuUser, Score


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

    def get_all_scores(self):
        return Score.objects.filter(
            user_stats__user_id__in=self.event_attendees.values_list("user_id"),
            date__gte=self.start_date,
            date__lte=self.end_date,
            mutation=ScoreMutation.NONE,
        )

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


class EventStats(models.Model):
    """Aggregated statistics for an event computed from all attendee scores."""

    id = models.BigAutoField(primary_key=True)
    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name="stats")

    total_scores = models.IntegerField()
    total_regular_hits = models.BigIntegerField()
    total_play_time = models.BigIntegerField()
    total_pp = models.FloatField()
    unique_players = models.IntegerField()
    unique_countries = models.IntegerField()
    unique_maps = models.IntegerField()
    last_updated = models.DateTimeField()

    def __str__(self):
        return f"Stats for {self.event.name}"


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


class BeatmapChallenge(models.Model):
    """Model representing a beatmap challenge for an event"""

    id = models.BigAutoField(primary_key=True)

    description = models.CharField()
    gamemode = models.IntegerField()
    challenge_type = models.CharField(
        choices=[
            (BeatmapChallengeType.BEST_COMBO, "Best Combo"),
            (BeatmapChallengeType.LOWEST_MISS_COUNT, "Lowest Miss Count"),
        ]
    )

    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="beatmap_challenges"
    )
    beatmap = models.ForeignKey(Beatmap, on_delete=models.CASCADE)

    def __str__(self):
        return f"[{self.event.name}] {self.description}"


class BeatmapChallengeScore(models.Model):
    """Through model linking a score to a beatmap challenge"""

    id = models.BigAutoField(primary_key=True)

    challenge = models.ForeignKey(BeatmapChallenge, on_delete=models.CASCADE)
    score = models.ForeignKey(
        Score, on_delete=models.CASCADE, related_name="beatmap_challenge_scores"
    )
    user = models.ForeignKey(
        OsuUser, on_delete=models.CASCADE, related_name="beatmap_challenge_scores"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["challenge", "user"], name="unique_challenge_user"
            )
        ]
