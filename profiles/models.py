from django.db import models
from django.db.models import Subquery, Case, When, F

import math
from datetime import datetime

import pytz
import oppaipy

from common.utils import get_beatmap_path
from common.osu import apiv1, utils
from common.osu.enums import Gamemode, BeatmapStatus
from profiles.enums import ScoreResult, ScoreSet

class OsuUserQuerySet(models.QuerySet):
    def non_restricted(self):
        return self.filter(disabled=False)

class OsuUser(models.Model):
    """
    Model representing an osu! user
    """

    # osu! data
    id = models.IntegerField(primary_key=True)
    username = models.CharField(max_length=30)
    country = models.CharField(max_length=2)
    join_date = models.DateTimeField()

    # Indicates restricted users
    disabled = models.BooleanField()

    objects = OsuUserQuerySet.as_manager()

    def __str__(self):
        return self.username

class UserStatsQuerySet(models.QuerySet):
    def non_restricted(self):
        return self.filter(user__disabled=False)

class UserStats(models.Model):
    """
    Model representing an osu! user's data relating to a specific gamemode
    """

    # osu! data
    gamemode = models.IntegerField()
    playcount = models.IntegerField()
    playtime = models.IntegerField()
    level = models.FloatField()
    ranked_score = models.BigIntegerField()
    total_score = models.BigIntegerField()
    rank = models.IntegerField()
    country_rank = models.IntegerField()
    pp = models.FloatField()
    accuracy = models.FloatField()
    count_300 = models.IntegerField()
    count_100 = models.IntegerField()
    count_50 = models.IntegerField()
    count_rank_ss = models.IntegerField()
    count_rank_ssh = models.IntegerField()
    count_rank_s = models.IntegerField()
    count_rank_sh = models.IntegerField()
    count_rank_a = models.IntegerField()

    # osu!chan calculated data
    extra_pp = models.FloatField()
    nochoke_pp = models.FloatField(null=True)   # null=True because at the moment only standard supports nochoke
    score_style_accuracy = models.FloatField()
    score_style_bpm = models.FloatField()
    score_style_cs = models.FloatField()
    score_style_ar = models.FloatField()
    score_style_od = models.FloatField()
    score_style_length = models.FloatField()

    # Relations
    user = models.ForeignKey(OsuUser, on_delete=models.CASCADE, related_name="stats")

    # Dates
    last_updated = models.DateTimeField(auto_now=True)

    objects = UserStatsQuerySet.as_manager()

    def add_scores_from_data(self, score_data_list):
        """
        Adds a list of scores and their beatmaps from the passed score_data_list.
        (requires all dicts to have beatmap_id set along with usual score data)
        """
        # Fetch beatmaps from database in bulk
        beatmap_ids = [int(s["beatmap_id"]) for s in score_data_list]
        beatmaps = list(Beatmap.objects.filter(id__in=beatmap_ids))

        beatmaps_to_create = []
        scores_from_data = []
        for score_data in score_data_list:
            score = Score()
            
            # Update Score fields
            score.score = int(score_data["score"])
            score.count_300 = int(score_data["count300"])
            score.count_100 = int(score_data["count100"])
            score.count_50 = int(score_data["count50"])
            score.count_miss = int(score_data["countmiss"])
            score.count_geki = int(score_data["countgeki"])
            score.count_katu = int(score_data["countkatu"])
            score.best_combo = int(score_data["maxcombo"])
            score.perfect = bool(int(score_data["perfect"]))
            score.mods = int(score_data["enabled_mods"])
            score.rank = score_data["rank"]
            score.date = datetime.strptime(score_data["date"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.UTC)

            # Update foreign keys
            # Search for beatmap in fetched, else create it
            beatmap_id = int(score_data["beatmap_id"])
            beatmap = next((beatmap for beatmap in beatmaps if beatmap.id == beatmap_id), None)
            if beatmap is None:
                beatmap = Beatmap.from_data(apiv1.get_beatmaps(beatmap_id=beatmap_id)[0])
                if beatmap.status not in [BeatmapStatus.APPROVED, BeatmapStatus.RANKED, BeatmapStatus.LOVED]:
                    continue
                beatmaps.append(beatmap)    # add to beatmaps incase another score is on this map
                beatmaps_to_create.append(beatmap)
            score.beatmap = beatmap
            score.user_stats = self

            # Update pp
            if "pp" in score_data and score_data["pp"] is not None:
                score.pp = float(score_data["pp"])
            else:
                # Check for gamemode
                if self.gamemode != Gamemode.STANDARD:
                    # We cant calculate pp for this mode yet so we need to disregard this score
                    continue
                # Use oppai to calculate pp
                with oppaipy.Calculator(get_beatmap_path(beatmap_id)) as calc:
                        calc.set_accuracy(count_100=score.count_100, count_50=score.count_50)
                        calc.set_misses(score.count_miss)
                        calc.set_combo(score.best_combo)
                        calc.set_mods(score.mods)
                        calc.calculate()
                        score.pp = calc.pp if math.isfinite(calc.pp) else 0
            
            # Update convenience fields
            score.gamemode = self.gamemode
            score.accuracy = utils.get_accuracy(score.count_300, score.count_100, score.count_50, score.count_miss, score.count_katu, score.count_geki, gamemode=self.gamemode)
            score.bpm = utils.get_bpm(beatmap.bpm, score.mods)
            score.length = utils.get_length(beatmap.drain_time, score.mods)
            score.circle_size = utils.get_cs(beatmap.circle_size, score.mods, score.gamemode)
            score.approach_rate = utils.get_ar(beatmap.approach_rate, score.mods)
            score.overall_difficulty = utils.get_od(beatmap.overall_difficulty, score.mods)

            # Process score
            score.process()

            scores_from_data.append(score)

        # Remove potential duplicates from a top 100 play also being in the recent 50
        scores_from_data = [score for score in scores_from_data if score == next(s for s in scores_from_data if s.date == score.date)]

        # Process scores for user stats values
        all_scores, scores_to_create = self.__process_scores(*scores_from_data)
        self.save()
        
        # Update new scores with newly saved UserStats id
        for score in scores_to_create:
            score.user_stats_id = self.id
        
        # Bulk add and update beatmaps and scores
        Beatmap.objects.bulk_create(beatmaps_to_create, ignore_conflicts=True)
        Score.objects.bulk_create(scores_to_create)

        # Update leaderboard memberships with all scores
        self.__update_memberships(*all_scores)

        # Return new scores
        return scores_to_create

    def __process_scores(self, *new_scores):
        """
        Calculates pp totals (extra pp, nochoke pp) and scores style using unique maps, and returns all scores for UserStats and the scores that need to be added
        """
        # Fetch all scores currently in database and add to new_scores ensuring no duplicate scores
        database_scores = self.scores.select_related("beatmap").filter(beatmap__status__in=[BeatmapStatus.RANKED, BeatmapStatus.APPROVED, BeatmapStatus.LOVED])
        database_score_dates = [score.date for score in database_scores]
        scores_to_create = [score for score in new_scores if score.date not in database_score_dates]
        scores = [*[score for score in scores_to_create if score.beatmap.status in [BeatmapStatus.RANKED, BeatmapStatus.APPROVED, BeatmapStatus.LOVED]], *database_scores]

        # Sort all scores by pp
        scores.sort(key=lambda s: s.pp, reverse=True)

        # Filter to be unique on maps (cant use .unique_maps() because duplicate maps might come from new scores)
        unique_map_scores = [score for score in scores if score == next(s for s in scores if s.beatmap_id == score.beatmap_id)]

        # Calculate bonus pp (+ pp from non-top100 scores)
        self.extra_pp = self.pp - utils.calculate_pp_total(score.pp for score in unique_map_scores[:100])

        # Calculate nochoke pp and mod pp
        if self.gamemode == Gamemode.STANDARD:
            self.nochoke_pp = utils.calculate_pp_total(sorted((score.nochoke_pp if score.result & ScoreResult.CHOKE else score.pp for score in unique_map_scores), reverse=True)) + self.extra_pp
        
        # Calculate score style
        top_100_scores = unique_map_scores[:100]  # score style limited to top 100 scores
        weighting_value = sum(0.95 ** i for i in range(100))
        self.score_style_accuracy = sum(score.accuracy * (0.95 ** i) for i, score in enumerate(top_100_scores)) / weighting_value
        self.score_style_bpm = sum(score.bpm * (0.95 ** i) for i, score in enumerate(top_100_scores)) / weighting_value
        self.score_style_length = sum(score.length * (0.95 ** i) for i, score in enumerate(top_100_scores)) / weighting_value
        self.score_style_cs = sum(score.circle_size * (0.95 ** i) for i, score in enumerate(top_100_scores)) / weighting_value
        self.score_style_ar = sum(score.approach_rate * (0.95 ** i) for i, score in enumerate(top_100_scores)) / weighting_value
        self.score_style_od = sum(score.overall_difficulty * (0.95 ** i) for i, score in enumerate(top_100_scores)) / weighting_value

        return scores, scores_to_create

    def __update_memberships(self, *scores):
        """
        Updates memberships this UserStats' OsuUser has with Leaderboards with the scores passed
        """
        memberships = self.user.memberships.select_for_update().select_related("leaderboard").filter(leaderboard__gamemode=self.gamemode)
        
        # Using through model so we can bulk add all scores for all memberships at once
        membership_score_model = Score.membership_set.through
        membership_scores_to_add = []

        for membership in memberships:
            # Find all scores matching criteria
            allowed_scores = [score for score in scores if membership.score_is_allowed(score)]
            # Filter for unique maps
            unique_map_scores = []
            beatmap_ids = []
            for score in allowed_scores:
                if score.beatmap_id not in beatmap_ids:
                    unique_map_scores.append(score)
                    beatmap_ids.append(score.beatmap_id)
            
            # Clear current scores so we can refresh them
            membership.scores.clear()

            # Create relations
            membership_scores = [membership_score_model(score=score, membership=membership) for score in unique_map_scores]
            membership_scores_to_add.extend(membership_scores)
            membership.pp = utils.calculate_pp_total(ms.score.pp for ms in membership_scores)
        
        # Bulk add scores to memberships and update memberships pp
        membership_score_model.objects.bulk_create(membership_scores_to_add, ignore_conflicts=True)
        self.user.memberships.bulk_update(memberships, ["pp"])

    def __str__(self):
        return "{}: {}".format(self.gamemode, self.user_id)

    class Meta:
        constraints = [
            # each user can only have 1 stats row per gamemode
            models.UniqueConstraint(fields=["user_id", "gamemode"], name="unique_user_stats")
        ]

        indexes = [
            # we are pretty much always going to be looking up via user related manager on gamemode
            #   (not sure if this works as intended with the foreign key but i imagine so)
            models.Index(fields=["user", "gamemode"])
        ]

class Beatmap(models.Model):
    """
    Model representing an osu! beatmap
    """

    # osu! data
    id = models.IntegerField(primary_key=True)
    set_id = models.IntegerField()
    artist = models.CharField(max_length=200)
    title = models.CharField(max_length=200)
    difficulty_name = models.CharField(max_length=200)
    gamemode = models.IntegerField()
    status = models.IntegerField()
    creator_name = models.CharField(max_length=30)
    bpm = models.FloatField()
    drain_time = models.IntegerField()
    total_time = models.IntegerField()
    max_combo = models.IntegerField(null=True)  # max_combo can be null for non-standard gamemodes
    circle_size = models.FloatField()
    overall_difficulty = models.FloatField()
    approach_rate = models.FloatField()
    health_drain = models.FloatField()
    star_rating = models.FloatField()
    submission_date = models.DateTimeField()
    approval_date = models.DateTimeField()
    last_updated = models.DateTimeField()
    
    # Relations
    # db_constraint=False because the creator might be restricted or otherwise not in the database
    # not using nullable, because we still want to have the creator_id field
    creator = models.ForeignKey(OsuUser, on_delete=models.DO_NOTHING, db_constraint=False, related_name="beatmaps")

    @classmethod
    def from_data(cls, beatmap_data):
        beatmap = cls(id=int(beatmap_data["beatmap_id"]))

        # Update fields
        beatmap.set_id = int(beatmap_data["beatmapset_id"])
        beatmap.artist = beatmap_data["artist"]
        beatmap.title = beatmap_data["title"]
        beatmap.difficulty_name = beatmap_data["version"]
        beatmap.gamemode = int(beatmap_data["mode"])
        beatmap.status = int(beatmap_data["approved"])
        beatmap.creator_name = beatmap_data["creator"]
        beatmap.bpm = float(beatmap_data["bpm"])
        beatmap.max_combo = int(beatmap_data["max_combo"]) if beatmap_data["max_combo"] != None else None
        beatmap.drain_time = int(beatmap_data["hit_length"])
        beatmap.total_time = int(beatmap_data["total_length"])
        beatmap.circle_size = float(beatmap_data["diff_size"])
        beatmap.overall_difficulty = float(beatmap_data["diff_overall"])
        beatmap.approach_rate = float(beatmap_data["diff_approach"])
        beatmap.health_drain = float(beatmap_data["diff_drain"])
        beatmap.star_rating = float(beatmap_data["difficultyrating"])
        beatmap.submission_date = datetime.strptime(beatmap_data["submit_date"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.UTC)
        beatmap.approval_date = datetime.strptime(beatmap_data["approved_date"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.UTC)
        beatmap.last_updated = datetime.strptime(beatmap_data["last_update"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.UTC)
        
        # Update foreign key ids
        beatmap.creator_id = int(beatmap_data["creator_id"])

        return beatmap

    def __str__(self):
        return "{} - {} [{}] (by {})".format(self.artist, self.title, self.difficulty_name, self.creator_name)

class ScoreQuerySet(models.QuerySet):
    def non_restricted(self):
        return self.filter(user_stats__user__disabled=False)

    def get_score_set(self, score_set=ScoreSet.NORMAL):
        """
        Queryset that returns distinct on beatmap_id prioritising highest pp given the score_set.
        Remember to use at end of query to not unintentionally filter out scores before primary filtering.
        """
        if score_set == ScoreSet.NORMAL:
            # always use pp
            scores = self.annotate(
                sorting_pp=F("pp")
            )
        elif score_set == ScoreSet.NEVER_CHOKE:
            # if choke use nochoke_pp, else use pp
            scores = self.annotate(
                sorting_pp=Case(
                    When(result=F("result").bitand(ScoreResult.CHOKE), then=F("nochoke_pp")),
                    default=F("pp"),
                    output_field=models.FloatField()
                )
            )
        elif score_set == ScoreSet.ALWAYS_FULL_COMBO:
            # always use nochoke_pp
            scores = self.annotate(
                sorting_pp=F("nochoke_pp")
            )

        # I do not like this query, but i cannot for the life of me figure out how to get django to SELECT FROM (...subquery...)
        # It seems after testing, the raw sql of these two queries (current one vs select from subquery), they were generally the same speed (on a tiny dataset)
        # I simply want to `return self.order_by("beatmap_id", "-pp").distinct("beatmap_id").order_by("-pp", "date")`, but this doesnt translate to a subquery
        # TODO: figure this out
        return scores.filter(
            id__in=Subquery(scores.all().order_by("beatmap_id", "-sorting_pp").distinct("beatmap_id").values("id"))
        ).order_by("-sorting_pp", "date")

class Score(models.Model):
    """
    Model representing an osu! score
    """

    # osu! data
    # auto pk because some legacy osu! api endpoints dont return score ids
    score = models.IntegerField()
    count_300 = models.IntegerField()
    count_100 = models.IntegerField()
    count_50 = models.IntegerField()
    count_miss = models.IntegerField()
    count_geki = models.IntegerField()
    count_katu = models.IntegerField()
    best_combo = models.IntegerField()
    perfect = models.BooleanField()
    mods = models.IntegerField()
    rank = models.CharField(max_length=3)
    pp = models.FloatField()
    date = models.DateTimeField()

    # Relations
    beatmap = models.ForeignKey(Beatmap, on_delete=models.CASCADE, related_name="scores")
    user_stats = models.ForeignKey(UserStats, on_delete=models.CASCADE, related_name="scores")

    # Convenience fields (derived from above fields)
    gamemode = models.IntegerField()
    accuracy = models.FloatField()
    bpm = models.FloatField()
    length = models.FloatField()
    circle_size = models.FloatField()
    approach_rate = models.FloatField()
    overall_difficulty = models.FloatField()

    # osu!chan calculated data
    # null=True because currently only osu standard supports nochoke/stars (since oppai only does)
    nochoke_pp = models.FloatField(null=True)
    star_rating = models.FloatField(null=True)
    result = models.IntegerField(null=True)

    objects = ScoreQuerySet.as_manager()

    def __process_score_result(self):
        if self.count_miss == 1:
            self.result = ScoreResult.ONE_MISS
            return
        
        pct_combo = self.best_combo / self.beatmap.max_combo

        if pct_combo == 1:
            self.result = ScoreResult.PERFECT
        elif pct_combo > 0.98 and self.count_miss == 0:
            self.result = ScoreResult.NO_BREAK
        elif pct_combo > 0.85:
            self.result = ScoreResult.END_CHOKE
        elif self.count_miss == 0:
            self.result = ScoreResult.SLIDER_BREAK
        else:
            self.result = ScoreResult.CLEAR

    def process(self):
        # calculate nochoke pp and result
        if self.user_stats.gamemode == Gamemode.STANDARD:
            # determine score result
            self.__process_score_result()
            # only need to pass beatmap_id, 100s, 50s, and mods since all other options default to best possible
            with oppaipy.Calculator(get_beatmap_path(self.beatmap_id)) as calc:
                calc.set_accuracy(count_100=self.count_100, count_50=self.count_50)
                calc.set_mods(self.mods)
                calc.calculate()
                self.nochoke_pp = calc.pp if math.isfinite(calc.pp) else 0
                self.star_rating = calc.stars if math.isfinite(calc.stars) else 0

    def __str__(self):
        return "{}: {:.0f}pp".format(self.beatmap_id, self.pp)

    class Meta:
        constraints = [
            # Scores are unique on user + date, so multiple scores from the same beatmaps + mods are allowed per user
            models.UniqueConstraint(fields=["user_stats_id", "date"], name="unique_score")
        ]

        indexes = [
            models.Index(fields=["pp"])
        ]
