from django.db import models

from minigames.enums import MinigameStatus
from profiles.models import OsuUser, Score, UserStats


class Minigame(models.Model):
    """
    Model representing a minigame instance
    """

    id = models.BigAutoField(primary_key=True)

    game_type = models.CharField()
    name = models.CharField()
    gamemode = models.IntegerField()
    status = models.CharField(
        choices=[
            (MinigameStatus.LOBBY, "Lobby"),
            (MinigameStatus.WAITING_TO_START, "Waiting to start"),
            (MinigameStatus.IN_PROGRESS, "In progress"),
            (MinigameStatus.FINALISING, "Finalising"),
            (MinigameStatus.FINISHED, "Finished"),
        ],
    )
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    config = models.JSONField()
    initial_state = models.JSONField(blank=True)
    state = models.JSONField(blank=True)
    state_last_computed = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    host = models.ForeignKey(OsuUser, on_delete=models.CASCADE)
    is_free_for_all = models.BooleanField()
    winning_team = models.OneToOneField(
        "MinigameTeam",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="won_minigame",
    )

    def get_unfinalised_players(self):
        """
        Returns a queryset of players whose scores have not been finalised
        """
        return UserStats.objects.filter(
            gamemode=self.gamemode,
            user__minigame_players__team__minigame=self,
            last_updated__lt=self.end_time,
        )

    def __str__(self):
        return self.name

    class Meta:
        indexes = [
            models.Index(fields=["game_type"]),
        ]


class MinigameTeam(models.Model):
    """
    Model representing a minigame team
    """

    id = models.BigAutoField(primary_key=True)

    name = models.CharField()
    points = models.FloatField()
    score_count = models.IntegerField()

    minigame = models.ForeignKey(
        Minigame, on_delete=models.CASCADE, related_name="teams"
    )

    def is_small_team(self):
        """
        Returns True if the team has less than 5 players
        """
        return self.players.count() < 5

    def __str__(self):
        return f"{self.minigame.name}: {self.name}"

    class Meta:
        ordering = ["id"]


class MinigamePlayer(models.Model):
    """
    Model representing a minigame player
    """

    id = models.BigAutoField(primary_key=True)

    points = models.FloatField()
    score_count = models.IntegerField()
    scores_last_updated = models.DateTimeField(null=True, blank=True)

    team = models.ForeignKey(
        MinigameTeam, on_delete=models.CASCADE, related_name="players"
    )
    user = models.ForeignKey(
        OsuUser, on_delete=models.CASCADE, related_name="minigame_players"
    )

    def __str__(self):
        return f"{self.user.username} ({self.team.name})"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["team", "user"], name="unique_minigame_player"
            )
        ]


class MinigameScore(models.Model):
    """
    Model representing a minigame score
    """

    id = models.BigAutoField(primary_key=True)

    score = models.ForeignKey(
        Score, on_delete=models.CASCADE, related_name="minigame_scores"
    )
    points = models.FloatField()

    minigame = models.ForeignKey(
        Minigame, on_delete=models.CASCADE, related_name="scores"
    )
    team = models.ForeignKey(
        MinigameTeam, on_delete=models.CASCADE, related_name="scores"
    )
    player = models.ForeignKey(
        MinigamePlayer, on_delete=models.CASCADE, related_name="scores"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["player", "score"], name="unique_minigame_score"
            )
        ]


class MinigameStats(models.Model):
    """
    Model representing an OsuUsers lifetime minigame stats
    """

    id = models.BigAutoField(primary_key=True)

    wins = models.IntegerField()

    user = models.OneToOneField(
        OsuUser, on_delete=models.CASCADE, related_name="minigame_stats"
    )
