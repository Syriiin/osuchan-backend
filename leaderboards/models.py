from django.db import models
from django.db.models import Q

from rest_framework.exceptions import PermissionDenied

from datetime import datetime

from common.osu.utils import calculate_pp_total
from common.osu.enums import BeatmapStatus
from profiles.enums import ScoreSet, ScoreResult
from profiles.models import OsuUser, Score, ScoreFilter
from leaderboards.enums import LeaderboardAccessType

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
            return self.distinct().filter(~Q(access_type=LeaderboardAccessType.PRIVATE) | Q(members__id=user_id) | Q(invitees__id=user_id))

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
    allow_past_scores = models.BooleanField(default=True)   # allow scores set before membership started
    member_count = models.IntegerField(null=True)   # global leaderboards will have null member count
    archived = models.BooleanField(default=False)

    # Relations
    score_filter = models.OneToOneField(ScoreFilter, on_delete=models.CASCADE)
    owner = models.ForeignKey(OsuUser, on_delete=models.CASCADE, related_name="owned_leaderboards", null=True, blank=True)
    members = models.ManyToManyField(OsuUser, through="Membership", related_name="leaderboards")
    invitees = models.ManyToManyField(OsuUser, through="Invite", related_name="invited_leaderboards")

    # Dates
    creation_time = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()
    global_leaderboards = GlobalLeaderboardManager()
    community_leaderboards = CommunityLeaderboardManager.from_queryset(CommunityLeaderboardQuerySet)()

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
            if self.access_type in (LeaderboardAccessType.PUBLIC_INVITE_ONLY, LeaderboardAccessType.PRIVATE) and self.owner_id != user_id:
                # Check if user has been invited
                try:
                    invitees = self.invitees.filter(id=user_id)
                except OsuUser.DoesNotExist:
                    raise PermissionDenied("You must be invited to join this leaderboard.")
                
                # Invite is being accepted
                self.invitees.remove(*invitees)

            # Create new membership
            membership = Membership(user_id=user_id, leaderboard=self)
            join_date = datetime.now()

        # Get scores
        scores = Score.objects.filter(
            user_stats__user_id=user_id,
            gamemode=self.gamemode
        )

        if not self.allow_past_scores:
            scores = scores.filter(date__gte=join_date)

        if self.score_filter:
            scores = scores.apply_score_filter(self.score_filter)
        
        scores = scores.get_score_set(score_set=self.score_set)
        membership.score_count = len(scores)    # len because we're evaluating the queryset anyway

        # Add scores to membership
        if self.score_set == ScoreSet.NORMAL:
            membership.pp = calculate_pp_total(score.pp for score in scores)
        elif self.score_set == ScoreSet.NEVER_CHOKE:
            membership.pp = calculate_pp_total(score.nochoke_pp if score.result & ScoreResult.CHOKE else score.pp for score in scores)
        elif self.score_set == ScoreSet.ALWAYS_FULL_COMBO:
            membership.pp = calculate_pp_total(score.nochoke_pp for score in scores)

        # Fetch rank
        membership.rank = self.memberships.filter(pp__gte=membership.pp).count() + 1
        
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
        return self.name

    class Meta:
        indexes = [
            models.Index(fields=["gamemode"])
        ]

class GlobalMembershipManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(leaderboard__access_type=LeaderboardAccessType.GLOBAL)

class CommunityMembershipManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().exclude(leaderboard__access_type=LeaderboardAccessType.GLOBAL)

class GlobalMembershipQuerySet(models.QuerySet):
    def non_restricted(self):
        return self.filter(user__disabled=False)

class CommunityMembershipQuerySet(GlobalMembershipQuerySet):
    def visible_to(self, user_id):
        # return memberships of leaderboards that are not private or that the user is a member/invitee of
        if user_id is None:
            return self.distinct().filter(~Q(leaderboard__access_type=LeaderboardAccessType.PRIVATE))
        else:
            return self.distinct().filter(~Q(leaderboard__access_type=LeaderboardAccessType.PRIVATE) | Q(leaderboard__members__id=user_id) | Q(leaderboard__invitees__id=user_id))

class Membership(models.Model):
    """
    Model representing the membership of a OsuUser to a Leaderboard
    """
    id = models.BigAutoField(primary_key=True)

    pp = models.FloatField()
    score_count = models.IntegerField()
    rank = models.IntegerField()
    
    # Relations
    leaderboard = models.ForeignKey(Leaderboard, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(OsuUser, on_delete=models.CASCADE, related_name="memberships")
    scores = models.ManyToManyField(Score)

    # Dates
    join_date = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()
    global_memberships = GlobalMembershipManager.from_queryset(GlobalMembershipQuerySet)()
    community_memberships = CommunityMembershipManager.from_queryset(CommunityMembershipQuerySet)()

    def __str__(self):
        return f"{self.leaderboard.name}: {self.user.username}"

    class Meta:
        indexes = [
            models.Index(fields=["leaderboard"]),
            models.Index(fields=["user"])
        ]

class Invite(models.Model):
    """
    Model representing an invitation of a OsuUser to a Leaderboard
    """
    id = models.BigAutoField(primary_key=True)

    message = models.TextField(blank=True)

    # Relations
    leaderboard = models.ForeignKey(Leaderboard, on_delete=models.CASCADE, related_name="invites")
    user = models.ForeignKey(OsuUser, on_delete=models.CASCADE, related_name="invites")

    # Dates
    invite_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.leaderboard.name}: {self.user.username}"

    class Meta:
        constraints = [
            # each user can only have 1 invite row per leaderboard
            models.UniqueConstraint(fields=["leaderboard_id", "user_id"], name="unique_invites")
        ]

        indexes = [
            models.Index(fields=["leaderboard"]),
            models.Index(fields=["user"])
        ]
