from django.db import models
from django.db.models import Q

from common.osu.utils import calculate_pp_total
from common.osu.enums import BeatmapStatus
from profiles.models import OsuUser, Score
from leaderboards.enums import AllowedBeatmapStatus, LeaderboardVisibility

class LeaderboardQuerySet(models.QuerySet):
    def visible_to(self, osu_user):
        # return leaderboards that are not private or that the user is a member of
        return self.distinct().filter(~Q(visibility=LeaderboardVisibility.PRIVATE) | Q(members=osu_user))

class Leaderboard(models.Model):
    """
    Model representing a leaderboard
    """

    gamemode = models.IntegerField()
    visibility = models.IntegerField()
    name = models.CharField(max_length=100)

    # score criteria
    allow_past_scores = models.BooleanField()   # allow scores set before membership started
    allowed_beatmap_status = models.IntegerField()
    oldest_beatmap_date = models.DateTimeField(null=True, blank=True)
    newest_beatmap_date = models.DateTimeField(null=True, blank=True)
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

    # Dates
    creation_time = models.DateTimeField(auto_now_add=True)

    objects = LeaderboardQuerySet.as_manager()

    def score_is_allowed(self, score):
        # Check against all criteria
        # this has got to be one of the ugliest functions iv ever written
        # TODO: clean this up by making it dynamic or something... (ie. all(self.passes_criterion(criterion, score) for criterion in criteria))
        return ((score.mods & self.required_mods == self.required_mods) and
                (score.mods & self.disqualified_mods == 0) and
                # beatmap status
                ((self.allowed_beatmap_status == AllowedBeatmapStatus.ANY) or
                    (self.allowed_beatmap_status == AllowedBeatmapStatus.LOVED_ONLY and score.beatmap.status == BeatmapStatus.LOVED) or
                    (self.allowed_beatmap_status == AllowedBeatmapStatus.RANKED_ONLY and score.beatmap.status in [BeatmapStatus.RANKED, BeatmapStatus.APPROVED])) and
                # optional filters
                (self.oldest_beatmap_date is None or self.oldest_beatmap_date < score.beatmap.last_updated) and
                (self.newest_beatmap_date is None or self.newest_beatmap_date > score.beatmap.last_updated) and
                (self.lowest_ar is None or self.lowest_ar < score.approach_rate) and
                (self.highest_ar is None or self.highest_ar > score.approach_rate) and
                (self.lowest_od is None or self.lowest_od < score.overall_difficulty) and
                (self.highest_od is None or self.highest_od > score.overall_difficulty) and
                (self.lowest_cs is None or self.lowest_cs < score.circle_size) and
                (self.highest_cs is None or self.highest_cs > score.circle_size) and
                (self.lowest_accuracy is None or self.lowest_accuracy < score.accuracy) and
                (self.highest_accuracy is None or self.highest_accuracy > score.accuracy))

    def update_membership(self, user_id):
        """
        Update a membership for a user_id ensuring all scores that fit the criteria are added
        """
        # Get or create Membership model
        try:
            membership = self.members.select_for_update().get(id=user_id)
        except OsuUser.DoesNotExist:
            membership = Membership(user_id=user_id, leaderboard=self)
        
        # Get scores
        scores = Score.objects.filter(
            user_stats__user_id=user_id,
            beatmap__gamemode=self.gamemode,
            mods__allbits=self.required_mods,
            mods__nobits=self.disqualified_mods
        )

        if self.allowed_beatmap_status == AllowedBeatmapStatus.LOVED_ONLY:
            scores = scores.filter(beatmap__status=BeatmapStatus.LOVED)
        elif self.allowed_beatmap_status == AllowedBeatmapStatus.RANKED_ONLY:
            scores = scores.filter(beatmap__status__in=[BeatmapStatus.RANKED, BeatmapStatus.APPROVED])

        # optional filters
        if self.oldest_beatmap_date:
            scores = scores.filter(beatmap__last_updated__gt=self.oldest_beatmap_date)
        if self.newest_beatmap_date:
            scores = scores.filter(beatmap__last_updated__lt=self.newest_beatmap_date)
        if self.lowest_ar:
            scores = scores.filter(approach_rate__gt=self.lowest_ar)
        if self.highest_ar:
            scores = scores.filter(approach_rate__lt=self.highest_ar)
        if self.lowest_od:
            scores = scores.filter(overall_difficulty__gt=self.lowest_od)
        if self.highest_od:
            scores = scores.filter(overall_difficulty__lt=self.highest_od)
        if self.lowest_cs:
            scores = scores.filter(circle_size__gt=self.lowest_cs)
        if self.highest_cs:
            scores = scores.filter(circle_size__lt=self.highest_cs)
        if self.lowest_accuracy:
            scores = scores.filter(accuracy__gt=self.lowest_accuracy)
        if self.highest_accuracy:
            scores = scores.filter(accuracy__lt=self.highest_accuracy)

        # Add scores to membership
        membership.pp = calculate_pp_total(score.pp for score in scores.order_by("-pp"))
        membership.save()
        membership.scores.add(*scores)

        return membership

    def __str__(self):
        return self.name

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

    def __str__(self):
        return f"{self.leaderboard.name}: {self.user_id}"

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
