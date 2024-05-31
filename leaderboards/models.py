import typing
from datetime import datetime

from django.db import models, transaction
from django.db.models import Max, Q
from rest_framework.exceptions import PermissionDenied

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

    def update_membership(self, user_id):
        """
        Update a membership for a user_id ensuring all scores that fit the criteria are added
        """
        # Dont't update memberships for archived leaderboards
        if self.archived:
            return

        # Get or create Membership model
        try:
            membership = self.memberships.select_for_update().get(user_id=user_id)
            # Clear all currently added scores
            membership.scores.clear()
            join_date = membership.join_date
        except Membership.DoesNotExist:
            if (
                self.access_type
                in (
                    LeaderboardAccessType.PUBLIC_INVITE_ONLY,
                    LeaderboardAccessType.PRIVATE,
                )
                and self.owner_id != user_id
            ):
                # Check if user has been invited
                try:
                    invitees = self.invitees.filter(id=user_id)
                except OsuUser.DoesNotExist:
                    raise PermissionDenied(
                        "You must be invited to join this leaderboard."
                    )

                # Invite is being accepted
                self.invitees.remove(*invitees)

            # Create new membership
            membership = Membership(user_id=user_id, leaderboard=self)
            join_date = datetime.now()

        # Get scores
        scores = Score.objects.filter(
            user_stats__user_id=user_id, gamemode=self.gamemode
        )

        if not self.allow_past_scores:
            scores = scores.filter(date__gte=join_date)

        if self.score_filter:
            scores = scores.apply_score_filter(self.score_filter)

        scores = scores.get_score_set(score_set=self.score_set)
        membership.score_count = len(
            scores
        )  # len because we're evaluating the queryset anyway

        # Add scores to membership
        if self.score_set == ScoreSet.NORMAL:
            membership.pp = calculate_pp_total(
                score.performance_total for score in scores
            )
        elif self.score_set == ScoreSet.NEVER_CHOKE:
            membership.pp = calculate_pp_total(
                (
                    score.nochoke_performance_total
                    if score.result & ScoreResult.CHOKE
                    else score.performance_total
                )
                for score in scores
            )
        elif self.score_set == ScoreSet.ALWAYS_FULL_COMBO:
            membership.pp = calculate_pp_total(
                score.nochoke_performance_total for score in scores
            )

        # Fetch rank
        membership.rank = self.memberships.filter(pp__gt=membership.pp).count() + 1

        if self.notification_discord_webhook_url != "":
            # Check for new top score
            pp_record = self.get_pp_record()
            player_top_score = scores.first()
            if (
                pp_record is not None
                and player_top_score is not None
                and player_top_score.performance_total > pp_record
            ):
                # TODO: fix this being here. needs to be here to avoid a circular import at the moment
                from leaderboards.tasks import send_leaderboard_top_score_notification

                # NOTE: need to use a function with default params here so the closure has the correct variables
                def send_notification(
                    leaderboard_id=self.id,
                    score_id=player_top_score.id,
                ):
                    send_leaderboard_top_score_notification.delay(
                        leaderboard_id, score_id
                    )

                transaction.on_commit(send_notification)

            # Check for new top player
            leaderboard_top_player = self.get_top_membership()
            if (
                leaderboard_top_player is not None
                and leaderboard_top_player.user_id != membership.user_id
                and membership.rank == 1
                and membership.pp > 0
            ):
                from leaderboards.tasks import send_leaderboard_top_player_notification

                # NOTE: need to use a function with default params here so the closure has the correct variables
                def send_notification(
                    leaderboard_id=self.id,
                    user_id=membership.user_id,
                ):
                    send_leaderboard_top_player_notification.delay(
                        leaderboard_id, user_id
                    )

                transaction.on_commit(send_notification)

        membership.save()
        membership.scores.add(*scores)

        return membership

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
