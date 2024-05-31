import typing

from django.db import models
from django.db.models import Max, Q

from common.osu.enums import Gamemode
from common.osu.utils import calculate_pp_total
from leaderboards.enums import LeaderboardAccessType
from profiles.enums import ScoreResult, ScoreSet
from profiles.models import OsuUser, Score, ScoreFilter


class GlobalLeaderboardManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(access_type=LeaderboardAccessType.GLOBAL)


class CommunityLeaderboardManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().exclude(access_type=LeaderboardAccessType.GLOBAL)


class CommunityLeaderboardQuerySet(models.QuerySet):
    def visible_to(self, user_id):
        # return leaderboards that are not private or that the user is a member/invitee of
        if user_id is None:
            return self.distinct().filter(~Q(access_type=LeaderboardAccessType.PRIVATE))
        else:
            return self.distinct().filter(
                ~Q(access_type=LeaderboardAccessType.PRIVATE)
                | Q(members__id=user_id)
                | Q(invitees__id=user_id)
            )


class Leaderboard(models.Model):
    """
    Model representing a leaderboard
    """

    id = models.BigAutoField(primary_key=True)

    gamemode = models.IntegerField()
    score_set = models.IntegerField()
    access_type = models.IntegerField()
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon_url = models.CharField(max_length=250, blank=True)
    allow_past_scores = models.BooleanField(
        default=True
    )  # allow scores set before membership started
    member_count = models.IntegerField(
        null=True, blank=True
    )  # global leaderboards will have null member count
    archived = models.BooleanField(default=False)
    notification_discord_webhook_url = models.CharField(max_length=250, blank=True)

    # Relations
    score_filter = models.OneToOneField(ScoreFilter, on_delete=models.CASCADE)
    owner = models.ForeignKey(
        OsuUser,
        on_delete=models.CASCADE,
        related_name="owned_leaderboards",
        null=True,
        blank=True,
    )
    members = models.ManyToManyField(
        OsuUser, through="Membership", related_name="leaderboards"
    )
    invitees = models.ManyToManyField(
        OsuUser, through="Invite", related_name="invited_leaderboards"
    )

    # Dates
    creation_time = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()
    global_leaderboards = GlobalLeaderboardManager()
    community_leaderboards = CommunityLeaderboardManager.from_queryset(
        CommunityLeaderboardQuerySet
    )()

    def get_pp_record(self) -> typing.Union[Score, None]:
        scores = Score.objects.non_restricted().filter(
            membership__leaderboard_id=self.id
        )

        scores = scores.annotate_sorting_pp(self.score_set)

        return scores.aggregate(Max("sorting_pp"))["sorting_pp__max"]

    def get_top_scores(self, limit=5):
        scores = (
            Score.objects.non_restricted()
            .distinct()
            .filter(membership__leaderboard_id=self.id)
            .select_related("user_stats", "user_stats__user", "beatmap")
            .get_score_set(score_set=self.score_set)
        )

        return scores[:limit]

    def get_top_membership(self):
        if self.access_type == LeaderboardAccessType.GLOBAL:
            memberships = Membership.global_memberships
        else:
            memberships = Membership.community_memberships

        return (
            memberships.non_restricted()
            .filter(leaderboard_id=self.id)
            .select_related("user")
            .order_by("-pp")
        ).first()

    def update_member_count(self):
        """
        Updates Leaderboard.member_count with the count of Leaderboard.memberships
        """
        self.member_count = self.members.count()
        self.save()

    def __str__(self):
        return f"[{Gamemode(self.gamemode).name}] {self.name}"

    class Meta:
        indexes = [models.Index(fields=["gamemode"])]


class GlobalMembershipManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(leaderboard__access_type=LeaderboardAccessType.GLOBAL)
        )


class CommunityMembershipManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .exclude(leaderboard__access_type=LeaderboardAccessType.GLOBAL)
        )


class GlobalMembershipQuerySet(models.QuerySet):
    def non_restricted(self):
        return self.filter(user__disabled=False)


class CommunityMembershipQuerySet(GlobalMembershipQuerySet):
    def visible_to(self, user_id):
        # return memberships of leaderboards that are not private or that the user is a member/invitee of
        if user_id is None:
            return self.distinct().filter(
                ~Q(leaderboard__access_type=LeaderboardAccessType.PRIVATE)
            )
        else:
            return self.distinct().filter(
                ~Q(leaderboard__access_type=LeaderboardAccessType.PRIVATE)
                | Q(leaderboard__members__id=user_id)
                | Q(leaderboard__invitees__id=user_id)
            )


class Membership(models.Model):
    """
    Model representing the membership of a OsuUser to a Leaderboard
    """

    id = models.BigAutoField(primary_key=True)

    pp = models.FloatField()
    score_count = models.IntegerField()
    rank = models.IntegerField()

    # Relations
    leaderboard = models.ForeignKey(
        Leaderboard, on_delete=models.CASCADE, related_name="memberships"
    )
    user = models.ForeignKey(
        OsuUser, on_delete=models.CASCADE, related_name="memberships"
    )
    scores = models.ManyToManyField(Score, through="MembershipScore")

    # Dates
    join_date = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()
    global_memberships = GlobalMembershipManager.from_queryset(
        GlobalMembershipQuerySet
    )()
    community_memberships = CommunityMembershipManager.from_queryset(
        CommunityMembershipQuerySet
    )()

    def recalculate(self):
        """
        Recalculates the memberships pp from its score list
        """
        if self.leaderboard.score_set == ScoreSet.NORMAL:
            self.pp = calculate_pp_total(
                score.performance_total
                for score in self.scores.order_by("-performance_total").all()
            )
        elif self.leaderboard.score_set == ScoreSet.NEVER_CHOKE:
            self.pp = calculate_pp_total(
                (
                    score.nochoke_performance_total
                    if score.result & ScoreResult.CHOKE
                    else score.performance_total
                )
                for score in self.scores.order_by("-performance_total").all()
            )
        elif self.leaderboard.score_set == ScoreSet.ALWAYS_FULL_COMBO:
            self.pp = calculate_pp_total(
                score.nochoke_performance_total
                for score in self.scores.order_by("-performance_total").all()
            )

    def __str__(self):
        return f"{self.leaderboard}: {self.user.username}"

    class Meta:
        indexes = [models.Index(fields=["leaderboard"]), models.Index(fields=["user"])]


class MembershipScore(models.Model):
    """
    Model representing a Score of a Membership
    """

    id = models.BigAutoField(primary_key=True)

    membership = models.ForeignKey(
        Membership, on_delete=models.CASCADE, related_name="membership_scores"
    )
    score = models.ForeignKey(
        Score, on_delete=models.CASCADE, related_name="membership_scores"
    )

    performance_total = models.FloatField()

    class Meta:
        indexes = [models.Index(fields=["performance_total"])]


class Invite(models.Model):
    """
    Model representing an invitation of a OsuUser to a Leaderboard
    """

    id = models.BigAutoField(primary_key=True)

    message = models.TextField(blank=True)

    # Relations
    leaderboard = models.ForeignKey(
        Leaderboard, on_delete=models.CASCADE, related_name="invites"
    )
    user = models.ForeignKey(OsuUser, on_delete=models.CASCADE, related_name="invites")

    # Dates
    invite_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.leaderboard}: {self.user.username}"

    class Meta:
        constraints = [
            # each user can only have 1 invite row per leaderboard
            models.UniqueConstraint(
                fields=["leaderboard_id", "user_id"], name="unique_invites"
            )
        ]

        indexes = [models.Index(fields=["leaderboard"]), models.Index(fields=["user"])]
