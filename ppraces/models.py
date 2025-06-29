from django.db import models

from ppraces.enums import PPRaceStatus
from profiles.models import OsuUser, Score


class PPRace(models.Model):
    """
    Model representing a pp race
    """

    id = models.BigAutoField(primary_key=True)

    name = models.CharField()
    gamemode = models.IntegerField()
    status = models.CharField(
        choices=[
            (PPRaceStatus.WAITING, "Waiting to start"),
            (PPRaceStatus.IN_PROGRESS, "In progress"),
            (PPRaceStatus.FINISHED, "Finished"),
        ]
    )
    duration = models.IntegerField()
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    calculator_engine = models.CharField()
    primary_performance_value = models.CharField()

    def __str__(self):
        return self.name


class PPRaceTeam(models.Model):
    """
    Model representing a team
    """

    id = models.BigAutoField(primary_key=True)

    name = models.CharField()
    total_pp = models.FloatField()
    score_count = models.IntegerField()

    pprace = models.ForeignKey(PPRace, on_delete=models.CASCADE, related_name="teams")
    members = models.ManyToManyField(
        OsuUser, through="PPRacePlayer", related_name="pprace_teams"
    )
    scores = models.ManyToManyField(
        Score, through="PPRaceScore", related_name="pprace_teams"
    )

    def __str__(self):
        return f"{self.pprace.name}: {self.name}"


class PPRacePlayer(models.Model):
    """
    Model representing a player
    """

    id = models.BigAutoField(primary_key=True)

    pp = models.FloatField()
    score_count = models.IntegerField()

    team = models.ForeignKey(
        PPRaceTeam, on_delete=models.CASCADE, related_name="players"
    )
    user = models.ForeignKey(
        OsuUser, on_delete=models.CASCADE, related_name="pprace_players"
    )
    scores = models.ManyToManyField(
        Score, through="PPRaceScore", related_name="pprace_players"
    )

    def __str__(self):
        return f"{self.user.username} ({self.team.name})"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["team_id", "user_id"], name="unique_pprace_player"
            )
        ]


class PPRaceScore(models.Model):
    """
    Model representing a score
    """

    id = models.BigAutoField(primary_key=True)

    score = models.ForeignKey(
        Score, on_delete=models.CASCADE, related_name="pprace_scores"
    )
    player = models.ForeignKey(
        PPRacePlayer, on_delete=models.CASCADE, related_name="pprace_scores"
    )
    team = models.ForeignKey(
        PPRaceTeam, on_delete=models.CASCADE, related_name="pprace_scores"
    )  # denormalised for performance

    performance_total = models.FloatField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["player_id", "score_id"], name="unique_pprace_score"
            )
        ]
