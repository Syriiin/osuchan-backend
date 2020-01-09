from django.db import models
from django.db.models import Q

from rest_framework.exceptions import PermissionDenied

from datetime import datetime

from common.osu.utils import calculate_pp_total
from common.osu.enums import BeatmapStatus
from profiles.models import OsuUser, Score
from leaderboards.enums import AllowedBeatmapStatus, LeaderboardAccessType

class LeaderboardQuerySet(models.QuerySet):
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

    gamemode = models.IntegerField()
    access_type = models.IntegerField()
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon_url = models.CharField(max_length=250, blank=True)

    # score criteria
    allow_past_scores = models.BooleanField()   # allow scores set before membership started
    allowed_beatmap_status = models.IntegerField()
    oldest_beatmap_date = models.DateTimeField(null=True, blank=True)
    newest_beatmap_date = models.DateTimeField(null=True, blank=True)
    oldest_score_date = models.DateTimeField(null=True, blank=True)
    newest_score_date = models.DateTimeField(null=True, blank=True)
    lowest_ar = models.FloatField(null=True, blank=True)
    highest_ar = models.FloatField(null=True, blank=True)
    lowest_od = models.FloatField(null=True, blank=True)
    highest_od = models.FloatField(null=True, blank=True)
    lowest_cs = models.FloatField(null=True, blank=True)
    highest_cs = models.FloatField(null=True, blank=True)
    required_mods = models.IntegerField()
    disqualified_mods = models.IntegerField()
    lowest_accuracy = models.FloatField(null=True, blank=True)
    highest_accuracy = models.FloatField(null=True, blank=True)

    # Relations
    owner = models.ForeignKey(OsuUser, on_delete=models.CASCADE, related_name="owned_leaderboards", null=True, blank=True)
    members = models.ManyToManyField(OsuUser, through="Membership", related_name="leaderboards")
    invitees = models.ManyToManyField(OsuUser, through="Invite", related_name="invited_leaderboards")

    # Dates
    creation_time = models.DateTimeField(auto_now_add=True)

    objects = LeaderboardQuerySet.as_manager()

    def score_is_allowed(self, score, membership):
        # Check against all criteria
        # this has got to be one of the ugliest functions iv ever written
        # TODO: clean this up by making it dynamic or something... (ie. all(self.passes_criterion(criterion, score) for criterion in criteria))
        return ((score.mods & self.required_mods == self.required_mods) and
                (score.mods & self.disqualified_mods == 0) and
                # past scores
                (self.allow_past_scores or score.date >= membership.join_date) and
                # beatmap status
                ((self.allowed_beatmap_status == AllowedBeatmapStatus.ANY) or
                    (self.allowed_beatmap_status == AllowedBeatmapStatus.LOVED_ONLY and score.beatmap.status == BeatmapStatus.LOVED) or
                    (self.allowed_beatmap_status == AllowedBeatmapStatus.RANKED_ONLY and score.beatmap.status in [BeatmapStatus.RANKED, BeatmapStatus.APPROVED])) and
                # optional filters
                (self.oldest_beatmap_date is None or self.oldest_beatmap_date <= score.beatmap.approval_date) and
                (self.newest_beatmap_date is None or self.newest_beatmap_date >= score.beatmap.approval_date) and
                (self.oldest_score_date is None or self.oldest_score_date <= score.date) and
                (self.newest_score_date is None or self.newest_score_date >= score.date) and
                (self.lowest_ar is None or self.lowest_ar <= score.approach_rate) and
                (self.highest_ar is None or self.highest_ar >= score.approach_rate) and
                (self.lowest_od is None or self.lowest_od <= score.overall_difficulty) and
                (self.highest_od is None or self.highest_od >= score.overall_difficulty) and
                (self.lowest_cs is None or self.lowest_cs <= score.circle_size) and
                (self.highest_cs is None or self.highest_cs >= score.circle_size) and
                (self.lowest_accuracy is None or self.lowest_accuracy <= score.accuracy) and
                (self.highest_accuracy is None or self.highest_accuracy >= score.accuracy))

    def update_membership(self, user_id):
        """
        Update a membership for a user_id ensuring all scores that fit the criteria are added
        """
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
                    invite = self.invitees.get(id=user_id)
                except OsuUser.DoesNotExist:
                    raise PermissionDenied("You must be invited to join this leaderboard.")
                
                # Invite is being accepted
                self.invitees.remove(invite)

            # Create new membership
            membership = Membership(user_id=user_id, leaderboard=self)
            join_date = datetime.now()

        # Get scores
        scores = Score.objects.filter(
            user_stats__user_id=user_id,
            beatmap__gamemode=self.gamemode,
            mods__allbits=self.required_mods,
            mods__nobits=self.disqualified_mods
        )

        if not self.allow_past_scores:
            scores = scores.filter(date__gte=join_date)

        if self.allowed_beatmap_status == AllowedBeatmapStatus.LOVED_ONLY:
            scores = scores.filter(beatmap__status=BeatmapStatus.LOVED)
        elif self.allowed_beatmap_status == AllowedBeatmapStatus.RANKED_ONLY:
            scores = scores.filter(beatmap__status__in=[BeatmapStatus.RANKED, BeatmapStatus.APPROVED])

        # optional filters
        if self.oldest_beatmap_date:
            scores = scores.filter(beatmap__approval_date__gte=self.oldest_beatmap_date)
        if self.newest_beatmap_date:
            scores = scores.filter(beatmap__approval_date__lte=self.newest_beatmap_date)
        if self.oldest_score_date:
            scores = scores.filter(date__gte=self.oldest_score_date)
        if self.newest_score_date:
            scores = scores.filter(date__lte=self.newest_score_date)
        if self.lowest_ar:
            scores = scores.filter(approach_rate__gte=self.lowest_ar)
        if self.highest_ar:
            scores = scores.filter(approach_rate__lte=self.highest_ar)
        if self.lowest_od:
            scores = scores.filter(overall_difficulty__gte=self.lowest_od)
        if self.highest_od:
            scores = scores.filter(overall_difficulty__lte=self.highest_od)
        if self.lowest_cs:
            scores = scores.filter(circle_size__gte=self.lowest_cs)
        if self.highest_cs:
            scores = scores.filter(circle_size__lte=self.highest_cs)
        if self.lowest_accuracy:
            scores = scores.filter(accuracy__gte=self.lowest_accuracy)
        if self.highest_accuracy:
            scores = scores.filter(accuracy__lte=self.highest_accuracy)

        scores = scores.unique_maps()

        # Add scores to membership
        membership.pp = calculate_pp_total(score.pp for score in scores)
        membership.save()
        membership.scores.add(*scores)

        return membership

    def __str__(self):
        return self.name

    class Meta:
        indexes = [
            models.Index(fields=["gamemode"])
        ]

class Membership(models.Model):
    """
    Model representing the membership of a OsuUser to a Leaderboard
    """

    pp = models.FloatField()
    
    # Relations
    leaderboard = models.ForeignKey(Leaderboard, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(OsuUser, on_delete=models.CASCADE, related_name="memberships")
    scores = models.ManyToManyField(Score)

    # Dates
    join_date = models.DateTimeField(auto_now_add=True)

    def score_is_allowed(self, score):
        return self.leaderboard.score_is_allowed(score, self)

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

    message = models.TextField(blank=True)

    # Relations
    leaderboard = models.ForeignKey(Leaderboard, on_delete=models.CASCADE, related_name="invites")
    user = models.ForeignKey(OsuUser, on_delete=models.CASCADE, related_name="invites")

    # Dates
    invite_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.leaderboard.name}: {self.user.username}"

    class Meta:
        indexes = [
            models.Index(fields=["leaderboard"]),
            models.Index(fields=["user"])
        ]

# Custom lookups

@models.fields.Field.register_lookup
class AllBits(models.Lookup):
    lookup_name = "allbits"

    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params + rhs_params
        return f"{lhs} & {rhs} = {rhs}", params

@models.fields.Field.register_lookup
class NoBits(models.Lookup):
    lookup_name = "nobits"

    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        return f"{lhs} & {rhs} = 0", params

