from django.db import models
from django.db.models import Subquery

from datetime import datetime

import pytz
import oppaipy

from common.utils import get_beatmap_path
from common.enums import ScoreResult
from common.osu import apiv1, utils
from common.osu.enums import Gamemode

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

    # used for marking players than suddenly disappear from osu api responses (user restricted)
    # TODO: testing on if this has a significant performance impact in places such as Score.objects.filter(user_stats__user__disabled=False)
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

    def add_scores_from_data(self, score_data_list, override_beatmap_id=None):
        """
        Efficiently adds a list of scores and their beatmaps from a passed list of scores
        """
        # If beatmap_id parameter passed, scores are all for the same beatmap
        if override_beatmap_id:
            user_scores = self.scores.select_for_update().filter(beatmap_id=override_beatmap_id)
            try:
                beatmap = Beatmap.objects.get(id=override_beatmap_id)
            except Beatmap.DoesNotExist:
                beatmap = Beatmap.from_data(apiv1.get_beatmaps(beatmap_id=override_beatmap_id)[0])
                beatmap.save()
        else:
            # Fetch all scores and beatmaps we need from database in bulk
            # NOTE: kinda inefficient, since we wont need all scores per beatmap (only ones with specific mods, but i dont know how to do that without raw sql)
            # TODO: maybe optimise this with raw sql?
            beatmap_ids = [int(s["beatmap_id"]) for s in score_data_list]
            user_scores = self.scores.select_for_update().filter(beatmap_id__in=beatmap_ids)
            beatmaps = Beatmap.objects.filter(id__in=beatmap_ids)

        # Iterate all scores fetched from osu api, setting fields and adding each to one of the following lists for bulk insertion/updating
        beatmaps_to_create = []
        scores_to_create = []
        scores_to_update = []
        unchanged_scores = []
        for score_data in score_data_list:
            beatmap_id = override_beatmap_id or int(score_data["beatmap_id"])
            
            # Get or create Score model (from prefetched list)
            try:
                score = next(score for score in user_scores if score.beatmap_id == beatmap_id and score.mods == int(score_data["enabled_mods"]))
                
                # Check if we actually need to update this score
                if score.date == datetime.strptime(score_data["date"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.UTC):
                    unchanged_scores.append(score)
                    continue
                
                scores_to_update.append(score)
            except StopIteration:
                score = Score()
                scores_to_create.append(score)
            
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
            score.pp = float(score_data["pp"])
            score.date = datetime.strptime(score_data["date"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.UTC)

            # Update foreign keys
            if not override_beatmap_id:
                # If not overriding beatmap, search for beatmap in fetched, else create it
                beatmap = next((beatmap for beatmap in beatmaps if beatmap.id == beatmap_id), None)
                if not beatmap:
                    beatmap = Beatmap.from_data(apiv1.get_beatmaps(beatmap_id=beatmap_id)[0])
                    beatmaps_to_create.append(beatmap)
            score.beatmap = beatmap
            score.user_stats_id = self.id
            
            # Update convenience fields
            score.accuracy = utils.get_accuracy(score.count_300, score.count_100, score.count_50, score.count_miss, score.count_katu, score.count_geki)
            score.bpm = utils.get_bpm(beatmap.bpm, score.mods)
            score.length = utils.get_length(beatmap.drain_time, score.mods)
            score.circle_size = utils.get_cs(beatmap.circle_size, score.mods)
            score.approach_rate = utils.get_ar(beatmap.approach_rate, score.mods)
            score.overall_difficulty = utils.get_od(beatmap.overall_difficulty, score.mods)

            # Process score
            score.process()

        # Process scores for user stats values
        self.__process_scores(*[*unchanged_scores, *scores_to_update, *scores_to_create])
        self.save()
        
        # Update new scores with newly saved UserStats id
        for score in scores_to_create:
            score.user_stats_id = self.id
        
        # Bulk add and update beatmaps and scores
        Score.objects.bulk_update(scores_to_update, [field.name for field in Score._meta.get_fields() if field.name != "id"])   # wish we didnt have to pass a field list to update all
        Beatmap.objects.bulk_create(beatmaps_to_create)
        Score.objects.bulk_create(scores_to_create)

        # Return new scores
        return unchanged_scores, scores_to_update, scores_to_create

    def __process_scores(self, *new_scores):
        """
        Calculates pp totals (extra pp, nochoke pp), scores style, adds new scores, and saves the model
        """
        
        # need to get list of unique map scores except the ones we already have (pk will only be set if we originally fetched this model rather than creating it)
        scores = [*new_scores, *self.scores.exclude(pk__in=[score.pk for score in new_scores if score.pk])]
        scores.sort(key=lambda s: s.pp, reverse=True)
        # need to filter to be unique on maps (cant use .unique_maps() because duplicate maps might come from new scores)
        scores = [score for score in scores if score == next(s for s in scores if s.beatmap_id == score.beatmap_id)]

        # calculate bonus pp (+ pp from non-top100 scores)
        self.extra_pp = self.pp - utils.calculate_pp_total(score.pp for score in scores[:100])

        # calculate nochoke pp and mod pp
        if self.gamemode == Gamemode.STANDARD:
            self.nochoke_pp = utils.calculate_pp_total(sorted((score.nochoke_pp if score.result & ScoreResult.CHOKE else score.pp for score in scores), reverse=True)) + self.extra_pp
        
        # TODO: modpp

        # score style
        top_100_scores = scores[:100]  # score style limited to top 100 scores
        weighting_value = sum(0.95 ** i for i in range(100))
        self.score_style_accuracy = sum(score.accuracy * (0.95 ** i) for i, score in enumerate(top_100_scores)) / weighting_value
        self.score_style_bpm = sum(score.bpm * (0.95 ** i) for i, score in enumerate(top_100_scores)) / weighting_value
        self.score_style_length = sum(score.length * (0.95 ** i) for i, score in enumerate(top_100_scores)) / weighting_value
        self.score_style_cs = sum(score.circle_size * (0.95 ** i) for i, score in enumerate(top_100_scores)) / weighting_value
        self.score_style_ar = sum(score.approach_rate * (0.95 ** i) for i, score in enumerate(top_100_scores)) / weighting_value
        self.score_style_od = sum(score.overall_difficulty * (0.95 ** i) for i, score in enumerate(top_100_scores)) / weighting_value

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
    last_updated = models.DateTimeField()
    
    # Relations
    # db_constraint=False because the creator might be restricted or otherwise not in the database
    # not using nullable, because we still want to have the creator_id field
    creator = models.ForeignKey(OsuUser, on_delete=models.DO_NOTHING, db_constraint=False, related_name="beatmaps")

    @classmethod
    def from_data(cls, beatmap_data):
        beatmap = cls(id=beatmap_data["beatmap_id"])

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
        beatmap.last_updated = datetime.strptime(beatmap_data["last_update"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.UTC)
        
        # Update foreign key ids
        beatmap.creator_id = int(beatmap_data["creator_id"])

        return beatmap

    def __str__(self):
        return "{} - {} [{}] (by {})".format(self.artist, self.title, self.difficulty_name, self.creator_name)

class ScoreQuerySet(models.QuerySet):
    def non_restricted(self):
        return self.filter(user_stats__user__disabled=False)

    def unique_maps(self):
        """
        Queryset that returns distinct on beatmap_id prioritising highest pp.
        Remember to use at end of query to not unintentially filter out scores before primary filtering.
        """
        # I do not like this query, but i cannot for the life of me figure out how to get django to SELECT FROM (...subquery...)
        # It seems after testing, the raw sql of these two queries (current one vs select from subquery), they were generally the same speed (on a tiny dataset)
        # I simply want to `return self.order_by("beatmap_id", "-pp").distinct("beatmap_id").order_by("-pp")`, but this doesnt translate to a subquery
        # TODO: figure this out
        return self.filter(
            id__in=Subquery(self.all().order_by("beatmap_id", "-pp").distinct("beatmap_id").values("id"))
        ).order_by("-pp")

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
            self.result = ScoreResult.ONEMISS
            return
        
        pct_combo = self.best_combo / self.beatmap.max_combo

        if pct_combo == 1:
            self.result = ScoreResult.PERFECT
        elif pct_combo > 0.98 and self.count_miss == 0:
            self.result = ScoreResult.NOBREAK
        elif pct_combo > 0.85:
            self.result = ScoreResult.ENDCHOKE
        elif self.count_miss == 0:
            self.result = ScoreResult.SLIDERBREAK
        else:
            self.result = ScoreResult.CLEAR

    def process(self):
        # calculate nochoke pp and result
        if self.beatmap.gamemode == Gamemode.STANDARD:
            # determine score result
            self.__process_score_result()
            # only need to pass beatmap_id, 100s, 50s, and mods since all other options default to best possible
            with oppaipy.Calculator(get_beatmap_path(self.beatmap_id)) as calc:
                calc.set_accuracy(count_100=self.count_100, count_50=self.count_50)
                calc.set_mods(self.mods)
                calc.calculate()
                self.nochoke_pp = calc.pp
                self.star_rating = calc.stars

    def __str__(self):
        return "{}: {:.0f}pp".format(self.beatmap_id, self.pp)

    class Meta:
        constraints = [
            # each user can only have 1 score row per beatmap + mods
            models.UniqueConstraint(fields=["user_stats_id", "beatmap_id", "mods"], name="unique_score")
        ]
