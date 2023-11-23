from datetime import datetime, timezone
from typing import Type

from django.db import models
from django.db.models import Case, F, Subquery, When

from common.error_reporter import ErrorReporter
from common.osu import utils
from common.osu.apiv1 import OsuApiV1
from common.osu.beatmap_provider import BeatmapProvider
from common.osu.difficultycalculator import (
    AbstractDifficultyCalculator,
    DifficultyCalculator,
    DifficultyCalculatorException,
)
from common.osu.enums import BeatmapStatus, Gamemode, Mods
from profiles.enums import AllowedBeatmapStatus, ScoreResult, ScoreSet


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
            # Only process "high scores" (highest scorev1 per mod per map per user) (need to make this distinction to prevent lazer scores from being treated as real)
            if score_data.get("score_id", None) is None:
                continue

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
            score.date = datetime.strptime(
                score_data["date"], "%Y-%m-%d %H:%M:%S"
            ).replace(tzinfo=timezone.utc)

            # Update foreign keys
            # Search for beatmap in fetched, else create it
            beatmap_id = int(score_data["beatmap_id"])
            beatmap = next(
                (beatmap for beatmap in beatmaps if beatmap.id == beatmap_id), None
            )
            if beatmap is None:
                osu_api_v1 = OsuApiV1()
                beatmap_data = osu_api_v1.get_beatmap(beatmap_id)
                if beatmap_data is None:
                    continue

                beatmap = Beatmap.from_data(beatmap_data)
                if (
                    beatmap.status
                    not in [
                        BeatmapStatus.APPROVED,
                        BeatmapStatus.RANKED,
                        BeatmapStatus.LOVED,
                    ]
                    or score.mods & Mods.UNRANKED != 0
                ):
                    # Skip unranked/unloved scores
                    continue
                beatmaps.append(
                    beatmap
                )  # add to beatmaps incase another score is on this map
                beatmaps_to_create.append(beatmap)
            score.beatmap = beatmap
            score.user_stats = self

            # Update pp
            if "pp" in score_data and score_data["pp"] is not None:
                score.performance_total = float(score_data["pp"])
                score.difficulty_calculator_engine = "legacy"
                score.difficulty_calculator_version = "legacy"
            else:
                # Check for gamemode
                if self.gamemode != Gamemode.STANDARD:
                    # We cant calculate pp for this mode yet so we need to disregard this score
                    continue

                beatmap_provider = BeatmapProvider()
                beatmap_path = beatmap_provider.get_beatmap_file(beatmap_id)

                if beatmap_path is None:
                    # TODO: log some sort of alert if this happens
                    continue

                with DifficultyCalculator(beatmap_path) as calc:
                    calc.set_accuracy(
                        count_100=score.count_100, count_50=score.count_50
                    )
                    calc.set_misses(score.count_miss)
                    calc.set_combo(score.best_combo)
                    calc.set_mods(score.mods)
                    calc.calculate()
                    score.performance_total = calc.performance_total
                    score.difficulty_calculator_engine = DifficultyCalculator.engine()
                    score.difficulty_calculator_version = DifficultyCalculator.version()

            # Update convenience fields
            score.gamemode = self.gamemode
            score.accuracy = utils.get_accuracy(
                score.count_300,
                score.count_100,
                score.count_50,
                score.count_miss,
                score.count_katu,
                score.count_geki,
                gamemode=self.gamemode,
            )
            score.bpm = utils.get_bpm(beatmap.bpm, score.mods)
            score.length = utils.get_length(beatmap.drain_time, score.mods)
            score.circle_size = utils.get_cs(
                beatmap.circle_size, score.mods, score.gamemode
            )
            score.approach_rate = utils.get_ar(beatmap.approach_rate, score.mods)
            score.overall_difficulty = utils.get_od(
                beatmap.overall_difficulty, score.mods
            )

            # Process score
            score.process()

            scores_from_data.append(score)

        # Remove potential duplicates from a top 100 play also being in the recent 50
        scores_to_create = [
            score
            for score in scores_from_data
            if score == next(s for s in scores_from_data if s.date == score.date)
        ]

        # Bulk add and update beatmaps and scores
        Beatmap.objects.bulk_create(beatmaps_to_create, ignore_conflicts=True)
        created_scores = Score.objects.bulk_create(
            scores_to_create, ignore_conflicts=True
        )

        # Recalculate with new scores added
        self.recalculate()
        self.save()

        # Return new scores
        return created_scores

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
                    BeatmapStatus.LOVED,
                ]
            )
            .order_by("-performance_total")
        )

        if len(scores) == 0:
            return

        # Filter to be unique on maps (cant use .unique_maps() because duplicate maps might come from new scores)
        #   (also this 1 liner is really inefficient for some reason so lets do it the standard way)
        # unique_map_scores = [score for score in scores if score == next(s for s in scores if s.beatmap_id == score.beatmap_id)]
        unique_map_scores = []
        beatmap_ids = []
        for score in scores:
            if score.beatmap_id not in beatmap_ids:
                unique_map_scores.append(score)
                beatmap_ids.append(score.beatmap_id)

        # Calculate bonus pp (+ pp from non-top100 scores)
        self.extra_pp = self.pp - utils.calculate_pp_total(
            score.performance_total for score in unique_map_scores[:100]
        )

        # Calculate score style
        top_100_scores = unique_map_scores[
            :100
        ]  # score style limited to top 100 scores
        weighting_value = sum(0.95**i for i in range(len(top_100_scores)))
        self.score_style_accuracy = (
            sum(score.accuracy * (0.95**i) for i, score in enumerate(top_100_scores))
            / weighting_value
        )
        self.score_style_bpm = (
            sum(score.bpm * (0.95**i) for i, score in enumerate(top_100_scores))
            / weighting_value
        )
        self.score_style_length = (
            sum(score.length * (0.95**i) for i, score in enumerate(top_100_scores))
            / weighting_value
        )
        self.score_style_cs = (
            sum(
                score.circle_size * (0.95**i)
                for i, score in enumerate(top_100_scores)
            )
            / weighting_value
        )
        self.score_style_ar = (
            sum(
                score.approach_rate * (0.95**i)
                for i, score in enumerate(top_100_scores)
            )
            / weighting_value
        )
        self.score_style_od = (
            sum(
                score.overall_difficulty * (0.95**i)
                for i, score in enumerate(top_100_scores)
            )
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
    artist = models.CharField(max_length=200)
    title = models.CharField(max_length=200)
    difficulty_name = models.CharField(max_length=200)
    gamemode = models.IntegerField()
    status = models.IntegerField()
    creator_name = models.CharField(max_length=30)
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

    # Difficulty values
    difficulty_total = models.FloatField()
    difficulty_calculator_engine = models.CharField(max_length=100)
    difficulty_calculator_version = models.CharField(max_length=100)

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
        beatmap.max_combo = (
            int(beatmap_data["max_combo"])
            if beatmap_data["max_combo"] != None
            else None
        )
        beatmap.drain_time = int(beatmap_data["hit_length"])
        beatmap.total_time = int(beatmap_data["total_length"])
        beatmap.circle_size = float(beatmap_data["diff_size"])
        beatmap.overall_difficulty = float(beatmap_data["diff_overall"])
        beatmap.approach_rate = float(beatmap_data["diff_approach"])
        beatmap.health_drain = float(beatmap_data["diff_drain"])
        beatmap.submission_date = datetime.strptime(
            beatmap_data["submit_date"], "%Y-%m-%d %H:%M:%S"
        ).replace(tzinfo=timezone.utc)
        beatmap.approval_date = (
            datetime.strptime(
                beatmap_data["approved_date"], "%Y-%m-%d %H:%M:%S"
            ).replace(tzinfo=timezone.utc)
            if beatmap_data["approved_date"] is not None
            else None
        )
        beatmap.last_updated = datetime.strptime(
            beatmap_data["last_update"], "%Y-%m-%d %H:%M:%S"
        ).replace(tzinfo=timezone.utc)

        beatmap.difficulty_total = float(beatmap_data["difficultyrating"])
        beatmap.difficulty_calculator_engine = "legacy"
        beatmap.difficulty_calculator_version = "legacy"

        # Update foreign key ids
        beatmap.creator_id = int(beatmap_data["creator_id"])

        return beatmap

    def update_difficulty_values(
        self, difficulty_calculator: Type[AbstractDifficultyCalculator]
    ):
        beatmap_provider = BeatmapProvider()
        beatmap_path = beatmap_provider.get_beatmap_file(self.id)

        if beatmap_path is None:
            # TODO: log some sort of alert if this happens
            return

        try:
            with difficulty_calculator(beatmap_path) as calculator:
                calculator.calculate()
                self.difficulty_total = calculator.difficulty_total
                self.difficulty_calculator_engine = difficulty_calculator.engine()
                self.difficulty_calculator_version = difficulty_calculator.version()
        except DifficultyCalculatorException as e:
            # TODO: handle this properly
            self.difficulty_total = 0
            self.difficulty_calculator_engine = difficulty_calculator.engine()
            self.difficulty_calculator_version = difficulty_calculator.version()
            error_reporter = ErrorReporter()
            error_reporter.report_error(e)

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
    calculator_engine = models.CharField(max_length=50)
    calculator_version = models.CharField(max_length=50)

    def __str__(self):
        if self.mods == 0:
            map_string = f"{self.beatmap_id}"
        else:
            map_string = f"{self.beatmap_id} +{utils.get_mods_string(self.mods)}"

        return f"{map_string}: {self.calculator_engine} ({self.calculator_version})"

    class Meta:
        constraints = [
            # Difficulty values are unique on beatmap + mods + calculator_engine + calculator_version
            # The implicit unique b-tree index on these columns is useful also
            models.UniqueConstraint(
                fields=[
                    "beatmap_id",
                    "mods",
                    "calculator_engine",
                    "calculator_version",
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

    name = models.CharField(max_length=20)
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

    def annotate_sorting_pp(self, score_set=ScoreSet.NORMAL):
        if score_set == ScoreSet.NEVER_CHOKE:
            # if choke use nochoke_performance_total, else use performance_total
            scores = self.annotate(
                sorting_pp=Case(
                    When(
                        result=F("result").bitand(ScoreResult.CHOKE),
                        then=F("nochoke_performance_total"),
                    ),
                    default=F("performance_total"),
                    output_field=models.FloatField(),
                )
            )
        elif score_set == ScoreSet.ALWAYS_FULL_COMBO:
            scores = self.annotate(sorting_pp=F("nochoke_performance_total"))
        else:
            scores = self.annotate(sorting_pp=F("performance_total"))

        return scores

    def get_score_set(self, score_set=ScoreSet.NORMAL):
        """
        Queryset that returns distinct on beatmap_id prioritising highest pp given the score_set.
        Remember to use at end of query to not unintentionally filter out scores before primary filtering.
        """
        scores = self.annotate_sorting_pp(score_set)

        return scores.filter(
            id__in=Subquery(
                scores.all()
                .order_by(
                    "beatmap_id",  # ordering first by beatmap_id is required for distinct
                    "-sorting_pp",  # required to make sure we dont distinct out the wrong scores
                )
                .distinct("beatmap_id")
                .values("id")
            )
        ).order_by("-sorting_pp", "date")


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
    best_combo = models.IntegerField()
    perfect = models.BooleanField()
    mods = models.IntegerField()
    rank = models.CharField(max_length=3)
    date = models.DateTimeField()

    # Relations
    beatmap = models.ForeignKey(
        Beatmap, on_delete=models.CASCADE, related_name="scores"
    )
    user_stats = models.ForeignKey(
        UserStats, on_delete=models.CASCADE, related_name="scores"
    )

    # Convenience fields (derived from above fields)
    gamemode = models.IntegerField()
    accuracy = models.FloatField()
    bpm = models.FloatField()
    length = models.FloatField()
    circle_size = models.FloatField()
    approach_rate = models.FloatField()
    overall_difficulty = models.FloatField()

    # Difficulty values
    # null=True because oppai only supports standard, and rosu-pp doesnt support converts
    performance_total = models.FloatField()
    nochoke_performance_total = models.FloatField(null=True, blank=True)
    difficulty_total = models.FloatField(null=True, blank=True)
    difficulty_calculator_engine = models.CharField(max_length=100)
    difficulty_calculator_version = models.CharField(max_length=100)

    # osu!chan calculated data
    # null=True because result types are only supported by standard at the moment
    result = models.IntegerField(null=True, blank=True)

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

            beatmap_provider = BeatmapProvider()
            beatmap_path = beatmap_provider.get_beatmap_file(self.beatmap_id)

            if beatmap_path is None:
                # TODO: log some sort of alert if this happens
                return

            # only need to pass beatmap_id, 100s, 50s, and mods since all other options default to best possible
            with DifficultyCalculator(beatmap_path) as calc:
                calc.set_accuracy(count_100=self.count_100, count_50=self.count_50)
                calc.set_mods(self.mods)
                calc.calculate()
                self.nochoke_performance_total = calc.performance_total
                self.difficulty_total = calc.difficulty_total
                self.difficulty_calculator_engine = "legacy"  # legacy because performance_total is still coming from the api response
                self.difficulty_calculator_version = "legacy"

    def update_performance_values(
        self, difficulty_calculator: Type[AbstractDifficultyCalculator]
    ):
        beatmap_provider = BeatmapProvider()
        beatmap_path = beatmap_provider.get_beatmap_file(self.beatmap_id)

        if beatmap_path is None:
            # TODO: log some sort of alert if this happens
            return

        try:
            with difficulty_calculator(beatmap_path) as calculator:
                # calculate nochoke
                calculator.set_accuracy(
                    count_100=self.count_100, count_50=self.count_50
                )
                calculator.set_mods(self.mods)
                calculator.calculate()
                self.nochoke_performance_total = calculator.performance_total
                self.difficulty_total = calculator.difficulty_total
                self.difficulty_calculator_engine = calculator.engine()
                self.difficulty_calculator_version = calculator.version()

                # calculate actual
                calculator.set_misses(self.count_miss)
                calculator.set_combo(self.best_combo)
                calculator.calculate()
                self.performance_total = calculator.performance_total
        except DifficultyCalculatorException as e:
            # TODO: handle this properly
            self.nochoke_performance_total = 0
            self.performance_total = 0
            self.difficulty_total = 0
            self.difficulty_calculator_engine = difficulty_calculator.engine()
            self.difficulty_calculator_version = difficulty_calculator.version()
            error_reporter = ErrorReporter()
            error_reporter.report_error(e)

    def __str__(self):
        return f"{self.beatmap_id}: {self.performance_total:.0f}pp"

    class Meta:
        constraints = [
            # Scores are unique on user + date, so multiple scores from the same beatmaps + mods are allowed per user
            models.UniqueConstraint(
                fields=["user_stats_id", "date"], name="unique_score"
            )
        ]

        indexes = [models.Index(fields=["performance_total"])]


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

    calculator_engine = models.CharField(max_length=50)
    calculator_version = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.score_id}: {self.calculator_engine} ({self.calculator_version})"

    class Meta:
        constraints = [
            # Performance values are unique on score + calculator_engine + calculator_version
            # The implicit unique b-tree index on these columns is useful also
            models.UniqueConstraint(
                fields=[
                    "score_id",
                    "calculator_engine",
                    "calculator_version",
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
        related_name="performance_calculations",
    )

    name = models.CharField(max_length=20)
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
