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
    # null=True because currently these fields are set after the scores are added (and adding scores requires the model to be saved (chicken and egg :<))
    extra_pp = models.FloatField(null=True)
    nochoke_pp = models.FloatField(null=True)

    # Relations
    user = models.ForeignKey(OsuUser, on_delete=models.CASCADE, related_name="stats")

    objects = UserStatsManager()

    def process_pp_totals(self):
        # calculate bonus pp (+ pp from non-top100 scores)
        self.extra_pp = self.pp - self.calculate_pp_total(score.pp for score in self.scores.order_by("-pp"))

        # calculate nochoke pp and mod pp
        self.nochoke_pp = self.calculate_pp_total(score.nochoke_pp for score in self.scores.order_by("-nochoke_pp")) + self.extra_pp
        # TODO: modpp

    def calculate_pp_total(self, sorted_pps):
        # sorted_pps should be a sorted generator but can be any iterable of floats
        print(len(list(sorted_pps)))
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

    # osu!chan calculated data
    # null=True because currently only osu standard supports nochoke (since oppai only does)
    nochoke_pp = models.FloatField(null=True)
    result = models.IntegerField(null=True)

    objects = ScoreManager()

    def process_score_result(self):
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

    def save(self, *args, **kwargs):
        # calculate nochoke pp before saving score
        if self.beatmap.gamemode == Gamemode.STANDARD:
            # determine score result
            self.process_score_result()
            # only need to pass beatmap_id, 100s, 50s, and mods since all other options default to best possible
            with oppaipy.Calculator(utils.get_beatmap_path(self.beatmap_id)) as calc:
                calc.set_accuracy(count_100=self.count_100, count_50=self.count_50)
                calc.set_mods(self.mods)
                calc.calculate()
                self.nochoke_pp = calc.pp
        super().save(*args, **kwargs)

    def __str__(self):
        return "{}: {:.0f}pp".format(self.beatmap_id, self.pp)
