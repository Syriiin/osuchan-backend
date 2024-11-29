from datetime import datetime, timezone

from django.db import models
from django.db.models import FilteredRelation, Q, Subquery

from common.osu import utils
from common.osu.difficultycalculator import (
    get_default_difficulty_calculator_class,
    get_difficulty_calculator_class_for_engine,
)
from common.osu.enums import BeatmapStatus, Gamemode, Mods
from common.osu.osuapi import BeatmapData
from profiles.enums import AllowedBeatmapStatus, ScoreMutation, ScoreResult, ScoreSet


class OsuUserQuerySet(models.QuerySet):
    def non_restricted(self):
        return self.filter(disabled=False)


class OsuUser(models.Model):
    """
    Model representing an osu! user
    """

    # osu! data
    id = models.IntegerField(primary_key=True)
    username = models.CharField()
    country = models.CharField()
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

    id = models.BigAutoField(primary_key=True)

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
    extra_pp = models.FloatField(default=0)
    score_style_accuracy = models.FloatField(default=0)
    score_style_bpm = models.FloatField(default=0)
    score_style_cs = models.FloatField(default=0)
    score_style_ar = models.FloatField(default=0)
    score_style_od = models.FloatField(default=0)
    score_style_length = models.FloatField(default=0)

    # Relations
    user = models.ForeignKey(OsuUser, on_delete=models.CASCADE, related_name="stats")

    # Dates
    last_updated = models.DateTimeField(auto_now=True)

    objects = UserStatsQuerySet.as_manager()

    def recalculate(self):
        """
        Calculates pp totals (extra pp, nochoke pp) and scores style using unique maps
        """
        # Fetch all scores currently in database and add to new_scores ensuring no duplicate scores
        scores = (
            self.scores.select_related("beatmap")
            .filter(
                beatmap__status__in=[
                    BeatmapStatus.RANKED,
                    BeatmapStatus.APPROVED,
                ]
            )
            .get_score_set(self.gamemode)[:100]
        )

        if len(scores) == 0:
            return

        # Calculate bonus pp (+ pp from non-top100 scores)
        self.extra_pp = self.pp - utils.calculate_pp_total(
            score.performance_total for score in scores[:100]
        )

        # Calculate score style
        weighting_value = sum(0.95**i for i in range(len(scores)))
        self.score_style_accuracy = (
            sum(score.accuracy * (0.95**i) for i, score in enumerate(scores))
            / weighting_value
        )
        self.score_style_bpm = (
            sum(score.bpm * (0.95**i) for i, score in enumerate(scores))
            / weighting_value
        )
        self.score_style_length = (
            sum(score.length * (0.95**i) for i, score in enumerate(scores))
            / weighting_value
        )
        self.score_style_cs = (
            sum(score.circle_size * (0.95**i) for i, score in enumerate(scores))
            / weighting_value
        )
        self.score_style_ar = (
            sum(score.approach_rate * (0.95**i) for i, score in enumerate(scores))
            / weighting_value
        )
        self.score_style_od = (
            sum(score.overall_difficulty * (0.95**i) for i, score in enumerate(scores))
            / weighting_value
        )

    def __str__(self):
        return f"{Gamemode(self.gamemode).name}: {self.user_id}"

    class Meta:
        constraints = [
            # each user can only have 1 stats row per gamemode
            models.UniqueConstraint(
                fields=["user_id", "gamemode"], name="unique_user_stats"
            )
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
    artist = models.CharField()
    title = models.CharField()
    difficulty_name = models.CharField()
    gamemode = models.IntegerField()
    status = models.IntegerField()
    creator_name = models.CharField()
    bpm = models.FloatField()
    drain_time = models.IntegerField()
    total_time = models.IntegerField()
    max_combo = models.IntegerField(
        null=True, blank=True
    )  # max_combo can be null for non-standard gamemodes
    circle_size = models.FloatField()
    overall_difficulty = models.FloatField()
    approach_rate = models.FloatField()
    health_drain = models.FloatField()
    submission_date = models.DateTimeField()
    approval_date = models.DateTimeField()
    last_updated = models.DateTimeField()

    # Relations
    # db_constraint=False because the creator might be restricted or otherwise not in the database
    # not using nullable, because we still want to have the creator_id field
    creator = models.ForeignKey(
        OsuUser,
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        related_name="beatmaps",
    )

    @classmethod
    def from_data(cls, beatmap_data: BeatmapData):
        beatmap = cls(id=beatmap_data.beatmap_id)

        beatmap.set_id = beatmap_data.set_id
        beatmap.gamemode = beatmap_data.gamemode
        beatmap.status = beatmap_data.status

        beatmap.artist = beatmap_data.artist
        beatmap.title = beatmap_data.title
        beatmap.difficulty_name = beatmap_data.difficulty_name

        beatmap.creator_name = beatmap_data.creator_name
        beatmap.creator_id = beatmap_data.creator_id

        beatmap.bpm = beatmap_data.bpm
        beatmap.max_combo = beatmap_data.max_combo
        beatmap.drain_time = beatmap_data.drain_time
        beatmap.total_time = beatmap_data.total_time

        beatmap.circle_size = beatmap_data.circle_size
        beatmap.overall_difficulty = beatmap_data.overall_difficulty
        beatmap.approach_rate = beatmap_data.approach_rate
        beatmap.health_drain = beatmap_data.health_drain

        beatmap.submission_date = beatmap_data.submission_date
        beatmap.last_updated = beatmap_data.last_updated
        beatmap.approval_date = beatmap_data.approval_date

        return beatmap

    def get_difficulty_calculation(self, calculator_engine: str | None = None):
        if calculator_engine is not None:
            calculator_engine_name = calculator_engine
        else:
            calculator_engine_name = get_default_difficulty_calculator_class(
                Gamemode(self.gamemode)
            ).engine()

        return DifficultyCalculation.objects.get(
            beatmap=self,
            mods=Mods.NONE,
            calculator_engine=calculator_engine_name,
        )

    def __str__(self):
        return "{} - {} [{}] (by {})".format(
            self.artist, self.title, self.difficulty_name, self.creator_name
        )


class DifficultyCalculation(models.Model):
    """
    Model representing a difficulty calculation of an osu! beatmap
    """

    id = models.BigAutoField(primary_key=True)

    beatmap = models.ForeignKey(
        Beatmap, on_delete=models.CASCADE, related_name="difficulty_calculations"
    )

    mods = models.IntegerField()
    calculator_engine = models.CharField()
    calculator_version = models.CharField()

    def get_total_difficulty(self):
        return self.difficulty_values.get(name="total").value

    def __str__(self):
        if self.mods == 0:
            map_string = f"{self.beatmap_id}"
        else:
            map_string = f"{self.beatmap_id} +{utils.get_mods_string(self.mods)}"

        return f"{map_string}: {self.calculator_engine} ({self.calculator_version})"

    class Meta:
        constraints = [
            # Difficulty calculations are unique on beatmap + mods + calculator_engine
            # The implicit unique b-tree index on these columns is useful also
            models.UniqueConstraint(
                fields=[
                    "beatmap_id",
                    "mods",
                    "calculator_engine",
                ],
                name="unique_difficulty_calculation",
            )
        ]


class DifficultyValue(models.Model):
    """
    Model representing a value of a difficulty calculation of an osu! beatmap
    """

    id = models.BigAutoField(primary_key=True)

    calculation = models.ForeignKey(
        DifficultyCalculation,
        on_delete=models.CASCADE,
        related_name="difficulty_values",
    )

    name = models.CharField()
    value = models.FloatField()

    def __str__(self):
        return f"{self.calculation_id}: {self.name} ({self.value})"

    class Meta:
        constraints = [
            # Difficulty values are unique on calculation + name
            # The implicit unique b-tree index on these columns is useful also
            models.UniqueConstraint(
                fields=[
                    "calculation_id",
                    "name",
                ],
                name="unique_difficulty_value",
            )
        ]

        indexes = [models.Index(fields=["value"])]


class ScoreQuerySet(models.QuerySet):
    def non_restricted(self):
        return self.filter(user_stats__user__disabled=False)

    def filter_mutations(self, mutations: list[ScoreMutation] | None = None):
        if mutations is None:
            mutations = [ScoreMutation.NONE]
        return self.filter(mutation__in=mutations)

    def apply_score_filter(self, score_filter):
        # Mods
        scores = self.filter(
            mods__allbits=score_filter.required_mods,
            mods__nobits=score_filter.disqualified_mods,
        )

        # Beatmap Status
        if score_filter.allowed_beatmap_status == AllowedBeatmapStatus.LOVED_ONLY:
            scores = scores.filter(beatmap__status=BeatmapStatus.LOVED)
        elif score_filter.allowed_beatmap_status == AllowedBeatmapStatus.RANKED_ONLY:
            scores = scores.filter(
                beatmap__status__in=[BeatmapStatus.RANKED, BeatmapStatus.APPROVED]
            )

        # Optional filters
        if score_filter.oldest_beatmap_date:
            scores = scores.filter(
                beatmap__approval_date__gte=score_filter.oldest_beatmap_date
            )
        if score_filter.newest_beatmap_date:
            scores = scores.filter(
                beatmap__approval_date__lte=score_filter.newest_beatmap_date
            )
        if score_filter.oldest_score_date:
            scores = scores.filter(date__gte=score_filter.oldest_score_date)
        if score_filter.newest_score_date:
            scores = scores.filter(date__lte=score_filter.newest_score_date)
        if score_filter.lowest_ar:
            scores = scores.filter(approach_rate__gte=score_filter.lowest_ar)
        if score_filter.highest_ar:
            scores = scores.filter(approach_rate__lte=score_filter.highest_ar)
        if score_filter.lowest_od:
            scores = scores.filter(overall_difficulty__gte=score_filter.lowest_od)
        if score_filter.highest_od:
            scores = scores.filter(overall_difficulty__lte=score_filter.highest_od)
        if score_filter.lowest_cs:
            scores = scores.filter(circle_size__gte=score_filter.lowest_cs)
        if score_filter.highest_cs:
            scores = scores.filter(circle_size__lte=score_filter.highest_cs)
        if score_filter.lowest_accuracy:
            scores = scores.filter(accuracy__gte=score_filter.lowest_accuracy)
        if score_filter.highest_accuracy:
            scores = scores.filter(accuracy__lte=score_filter.highest_accuracy)
        if score_filter.lowest_length:
            scores = scores.filter(length__gte=score_filter.lowest_length)
        if score_filter.highest_length:
            scores = scores.filter(length__lte=score_filter.highest_length)

        return scores

    def get_score_set(
        self,
        gamemode: Gamemode,
        score_set: ScoreSet = ScoreSet.NORMAL,
        calculator_engine: str | None = None,
        primary_performance_value: str = "total",
    ):
        """
        Queryset that returns distinct on beatmap_id prioritising highest pp given the score_set.
        Remember to use at end of query to not unintentionally filter out scores before primary filtering.
        """
        gamemode_scores = self.filter(gamemode=gamemode)
        if score_set == ScoreSet.NORMAL:
            scores = gamemode_scores.filter_mutations([ScoreMutation.NONE])
        elif score_set == ScoreSet.NEVER_CHOKE:
            scores = gamemode_scores.filter_mutations(
                [ScoreMutation.NONE, ScoreMutation.NO_CHOKE]
            )
        else:
            raise ValueError(f"Invalid score set: {score_set}")

        difficulty_calculator_class = (
            get_default_difficulty_calculator_class(gamemode)
            if calculator_engine is None
            else get_difficulty_calculator_class_for_engine(calculator_engine)
        )

        annotated_scores = (
            scores.annotate(
                performance_calculation=FilteredRelation(
                    "performance_calculations",
                    condition=Q(
                        performance_calculations__calculator_engine=difficulty_calculator_class.engine()
                    ),
                )
            )
            .annotate(
                performance_value=FilteredRelation(
                    "performance_calculation__performance_values",
                    condition=Q(
                        performance_calculation__performance_values__name=primary_performance_value
                    ),
                )
            )
            .annotate(performance_total=models.F("performance_value__value"))
        )

        return annotated_scores.filter(
            id__in=Subquery(
                annotated_scores.all()
                .order_by(
                    "beatmap_id",  # ordering first by beatmap_id is required for distinct
                    "-performance_total",  # required to make sure we dont distinct out the wrong scores
                )
                .distinct("beatmap_id")
                .values("id")
            )
        ).order_by("-performance_total", "date")


class Score(models.Model):
    """
    Model representing an osu! score
    """

    id = models.BigAutoField(primary_key=True)

    # osu! data
    # auto pk because some legacy osu! api endpoints dont return score ids
    score = models.IntegerField()
    count_300 = models.IntegerField()
    count_100 = models.IntegerField()
    count_50 = models.IntegerField()
    count_miss = models.IntegerField()
    count_geki = models.IntegerField()
    count_katu = models.IntegerField()
    statistics = models.JSONField()
    best_combo = models.IntegerField()
    perfect = models.BooleanField()
    mods = models.IntegerField()
    is_classic = models.BooleanField()
    rank = models.CharField()
    date = models.DateTimeField()

    # Relations
    beatmap = models.ForeignKey(
        Beatmap, on_delete=models.CASCADE, related_name="scores"
    )
    user_stats = models.ForeignKey(
        UserStats, on_delete=models.CASCADE, related_name="scores"
    )
    original_score = models.ForeignKey(
        "Score",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="mutations",
    )

    # Convenience fields (derived from above fields)
    gamemode = models.IntegerField()
    accuracy = models.FloatField()
    bpm = models.FloatField()
    length = models.FloatField()
    circle_size = models.FloatField()
    approach_rate = models.FloatField()
    overall_difficulty = models.FloatField()

    # osu!chan calculated data
    # null=True because result types are only supported by standard at the moment
    result = models.IntegerField(null=True, blank=True)
    mutation = models.IntegerField()

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

    def get_nochoke_mutation(self):
        """
        Returns a copy of the score with nochoke mutations applied
        """
        gamemode = Gamemode(self.gamemode)
        if gamemode != Gamemode.STANDARD:
            raise ValueError(
                "Nochoke mutations are only supported for standard gamemode"
            )
        if not self.result & ScoreResult.CHOKE:
            raise ValueError("Nochoke mutations can only be applied to choke scores")

        # Copy base attributes
        score = Score(
            score=self.score,
            count_geki=self.count_geki,
            count_katu=self.count_katu,
            mods=self.mods,
            is_classic=self.is_classic,
            date=self.date,
            beatmap=self.beatmap,
            user_stats=self.user_stats,
            original_score=self,
            gamemode=gamemode,
            bpm=self.bpm,
            length=self.length,
            circle_size=self.circle_size,
            approach_rate=self.approach_rate,
            overall_difficulty=self.overall_difficulty,
        )

        # Adjust unchoked
        score.result = ScoreResult.PERFECT
        score.mutation = ScoreMutation.NO_CHOKE

        score.count_300 = self.count_300 + self.count_miss
        score.count_100 = self.count_100
        score.count_50 = self.count_50
        score.count_miss = 0
        score.statistics = {
            "great": score.count_300,
            "ok": score.count_100,
            "meh": score.count_50,
            "miss": score.count_miss,
        }
        score.best_combo = self.beatmap.max_combo
        score.perfect = True

        # Calculate new accuracy
        score.accuracy = utils.get_classic_accuracy(
            score.statistics,
            gamemode=gamemode,
        )
        if score.accuracy == 1:
            if score.mods & Mods.HIDDEN or score.mods & Mods.FLASHLIGHT:
                score.rank = "XH"
            else:
                score.rank = "X"
        else:
            if score.mods & Mods.HIDDEN or score.mods & Mods.FLASHLIGHT:
                score.rank = "SH"
            else:
                score.rank = "S"

        return score

    def get_performance_calculation(self, calculator_engine: str | None = None):
        if calculator_engine is not None:
            calculator_engine_name = calculator_engine
        else:
            calculator_engine_name = get_default_difficulty_calculator_class(
                Gamemode(self.gamemode)
            ).engine()

        return PerformanceCalculation.objects.get(
            score=self,
            calculator_engine=calculator_engine_name,
        )

    def __str__(self):
        return f"{Gamemode(self.gamemode).name} {self.id}"

    class Meta:
        constraints = [
            # Scores are unique on user + date + mutation, so multiple scores from the same beatmaps + mods are allowed per user, as well as mutations
            models.UniqueConstraint(
                fields=["user_stats_id", "date", "mutation"], name="unique_score"
            )
        ]


class ScoreFilter(models.Model):
    id = models.BigAutoField(primary_key=True)
    allowed_beatmap_status = models.IntegerField(
        default=AllowedBeatmapStatus.RANKED_ONLY
    )
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
    required_mods = models.IntegerField(default=Mods.NONE)
    disqualified_mods = models.IntegerField(default=Mods.NONE)
    lowest_accuracy = models.FloatField(null=True, blank=True)
    highest_accuracy = models.FloatField(null=True, blank=True)
    lowest_length = models.FloatField(null=True, blank=True)
    highest_length = models.FloatField(null=True, blank=True)


class PerformanceCalculation(models.Model):
    """
    Model representing a performance calculation of an osu! score
    """

    # TODO: consider using uuid to avoid bulk_create issue
    id = models.BigAutoField(primary_key=True)

    score = models.ForeignKey(
        Score, on_delete=models.CASCADE, related_name="performance_calculations"
    )
    difficulty_calculation = models.ForeignKey(
        DifficultyCalculation,
        on_delete=models.CASCADE,
        related_name="performance_calculations",
    )

    calculator_engine = models.CharField()
    calculator_version = models.CharField()

    def get_total_performance(self):
        return self.performance_values.get(name="total").value

    def __str__(self):
        return f"{self.score_id}: {self.calculator_engine} ({self.calculator_version})"

    class Meta:
        constraints = [
            # Performance calculations are unique on score + calculator_engine
            # The implicit unique b-tree index on these columns is useful also
            models.UniqueConstraint(
                fields=[
                    "score_id",
                    "calculator_engine",
                ],
                name="unique_performance_calculation",
            )
        ]


class PerformanceValue(models.Model):
    """
    Model representing a value of a performance calculation of an osu! score
    """

    id = models.BigAutoField(primary_key=True)

    calculation = models.ForeignKey(
        PerformanceCalculation,
        on_delete=models.CASCADE,
        related_name="performance_values",
    )

    name = models.CharField()
    value = models.FloatField()

    def __str__(self):
        return f"{self.calculation_id}: {self.name} ({self.value})"

    class Meta:
        constraints = [
            # Performance values are unique on calculation + name
            # The implicit unique b-tree index on these columns is useful also
            models.UniqueConstraint(
                fields=[
                    "calculation_id",
                    "name",
                ],
                name="unique_performance_value",
            )
        ]

        indexes = [models.Index(fields=["value"])]


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
