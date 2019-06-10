from django.db import models

import oppaipy

from common import utils
from common.enums import ScoreResult
from common.osu.enums import Gamemode
from profiles.managers import OsuUserManager, UserStatsManager, BeatmapManager, ScoreManager

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

    objects = OsuUserManager()

    def __str__(self):
        return self.username

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

    objects = UserStatsManager()

    def process_and_add_scores(self, *new_scores):
        """
        Calculates pp totals (extra pp, nochoke pp), scores style, adds new scores, and saves the model
        """
        
        # need to get list of unique map scores except the ones we already have (pk will only be set if we originally fetched this model rather than creating it)
        scores = [*new_scores, *self.scores.exclude(pk__in=[score.pk for score in new_scores if score.pk])]
        scores.sort(key=lambda s: s.pp, reverse=True)
        # need to filter to be unique on maps (cant use .unique_maps() because duplicate maps might come from new scores)
        scores = [score for score in scores if score == next(s for s in scores if s.beatmap_id == score.beatmap_id)]

        # calculate bonus pp (+ pp from non-top100 scores)
        self.extra_pp = self.pp - self.calculate_pp_total(score.pp for score in scores[:100])

        # calculate nochoke pp and mod pp
        if self.gamemode == Gamemode.STANDARD:
            self.nochoke_pp = self.calculate_pp_total(sorted((score.nochoke_pp if score.result & ScoreResult.CHOKE else score.pp for score in scores), reverse=True)) + self.extra_pp
        
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
        
        self.save()
        self.scores.add(*new_scores, bulk=False)

    def calculate_pp_total(self, sorted_pps):
        # sorted_pps should be a sorted generator but can be any iterable of floats
        return sum(pp * (0.95 ** i) for i, pp in enumerate(sorted_pps))

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

    objects = BeatmapManager()

    def __str__(self):
        return "{} - {} [{}] (by {})".format(self.artist, self.title, self.difficulty_name, self.creator_name)

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

    objects = ScoreManager()

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
        # calculate nochoke pp and result before saving score
        if self.beatmap.gamemode == Gamemode.STANDARD:
            # determine score result
            self.__process_score_result()
            # only need to pass beatmap_id, 100s, 50s, and mods since all other options default to best possible
            with oppaipy.Calculator(utils.get_beatmap_path(self.beatmap_id)) as calc:
                calc.set_accuracy(count_100=self.count_100, count_50=self.count_50)
                calc.set_mods(self.mods)
                calc.calculate()
                self.nochoke_pp = calc.pp
                self.star_rating = calc.stars

    def __str__(self):
        return "{}: {:.0f}pp".format(self.beatmap_id, self.pp)
