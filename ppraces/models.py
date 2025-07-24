from django.db import models

from ppraces.enums import PPRaceStatus
from profiles.models import OsuUser, Score, UserStats


class PPRace(models.Model):
    """
    Model representing a pp race
    """

    id = models.BigAutoField(primary_key=True)

    name = models.CharField()
    gamemode = models.IntegerField()
    status = models.CharField(
        choices=[
            (PPRaceStatus.LOBBY, "Lobby"),
            (PPRaceStatus.WAITING_TO_START, "Waiting to start"),
            (PPRaceStatus.IN_PROGRESS, "In progress"),
            (PPRaceStatus.FINALISING, "Finalising"),
            (PPRaceStatus.FINISHED, "Finished"),
        ]
    )
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    pp_decay_base = models.FloatField()
    calculator_engine = models.CharField()
    primary_performance_value = models.CharField()

    def get_recent_scores(self):
        """
        Returns the most recent scores for this
        """
        return Score.objects.filter(
            pprace_scores__team__pprace=self,
        ).order_by(
            "-date"
        )[:50]

    def all_players_finalised(self) -> bool:
        """
        Returns True if all players last update is past the end time
        """
        return not UserStats.objects.filter(
            gamemode=self.gamemode,
            user__pprace_players__team__pprace=self,
            last_updated__lt=self.end_time,
        ).exists()

    def get_unfinalised_players(self):
        """
        Returns a queryset of players whose scores have not been finalised
        """
        return UserStats.objects.filter(
            gamemode=self.gamemode,
            user__pprace_players__team__pprace=self,
            last_updated__lt=self.end_time,
        )

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

    def get_top_scores(self):
        """
        Returns the top scores for this team
        """
        return self.scores.get_score_set(self.pprace.gamemode)[:100]

    def is_small_team(self):
        """
        Returns True if the team has less than 5 players
        """
        return self.players.count() < 5

    def __str__(self):
        return f"{self.pprace.name}: {self.name}"

    class Meta:
        ordering = ["id"]


class PPRacePlayer(models.Model):
    """
    Model representing a player
    """

    id = models.BigAutoField(primary_key=True)

    pp = models.FloatField()
    pp_contribution = models.FloatField()
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
