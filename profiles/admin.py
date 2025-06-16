from django.contrib import admin

from common.osu import utils
from common.osu.enums import BeatmapStatus, BitMods, Gamemode
from profiles.enums import ScoreMutation, ScoreResult
from profiles.models import (
    Beatmap,
    DifficultyCalculation,
    DifficultyValue,
    OsuUser,
    PerformanceCalculation,
    PerformanceValue,
    Score,
    ScoreFilter,
    UserStats,
)


class OsuUserAdmin(admin.ModelAdmin):
    model = OsuUser

    list_display = [
        "__str__",
        "id",
        "country",
        "join_date",
    ]


class UserStatsAdmin(admin.ModelAdmin):
    model = UserStats
    raw_id_fields = ("user",)

    list_display = [
        "id",
        "gamemode_display",
        "user",
        "rank",
        "pp",
    ]
    list_filter = ["gamemode"]

    @admin.display(description="Gamemode")
    def gamemode_display(self, obj: UserStats):
        return Gamemode(obj.gamemode).name


class BeatmapAdmin(admin.ModelAdmin):
    model = Beatmap
    raw_id_fields = ("creator",)

    list_display = [
        "__str__",
        "gamemode_display",
        "status_display",
        "submission_date",
        "last_updated",
        "approval_date",
    ]
    list_filter = ["gamemode", "status"]

    @admin.display(description="Gamemode")
    def gamemode_display(self, obj: Beatmap):
        return Gamemode(obj.gamemode).name

    @admin.display(description="Status")
    def status_display(self, obj: Beatmap):
        return BeatmapStatus(obj.status).name


class DifficultyCalculationAdmin(admin.ModelAdmin):
    model = DifficultyCalculation
    raw_id_fields = ("beatmap",)

    list_display = [
        "id",
        "beatmap",
        "mods_display",
        "calculator_engine",
        "calculator_version",
    ]
    list_filter = ["calculator_engine"]
    # NOTE: for some reason it's automatically joining on beatmap__creator unless we explicitly list_select_related
    list_select_related = ["beatmap"]

    @admin.display(description="Mods")
    def mods_display(self, obj: DifficultyCalculation):
        if obj.mods == BitMods.NONE:
            return None
        return utils.get_mods_string(obj.mods)


class DifficultyValueAdmin(admin.ModelAdmin):
    model = DifficultyValue
    raw_id_fields = ("calculation",)

    list_display = [
        "id",
        "beatmap_display",
        "mods_display",
        "calculator_engine_display",
        "calculator_version_display",
        "name",
        "value",
    ]
    list_filter = ["calculation__calculator_engine", "name"]
    # NOTE: for some reason it's automatically joining on beatmap__creator unless we explicitly list_select_related
    list_select_related = ["calculation__beatmap"]

    @admin.display(description="Mods")
    def mods_display(self, obj: DifficultyValue):
        if obj.calculation.mods == BitMods.NONE:
            return None
        return utils.get_mods_string(obj.calculation.mods)

    @admin.display(description="Beatmap")
    def beatmap_display(self, obj: DifficultyValue):
        return obj.calculation.beatmap

    @admin.display(description="Calculator Engine")
    def calculator_engine_display(self, obj: DifficultyValue):
        return obj.calculation.calculator_engine

    @admin.display(description="Calculator Version")
    def calculator_version_display(self, obj: DifficultyValue):
        return obj.calculation.calculator_version


class ScoreAdmin(admin.ModelAdmin):
    model = Score
    raw_id_fields = (
        "beatmap",
        "user_stats",
        "original_score",
    )

    list_display = [
        "__str__",
        "user",
        "mods_display",
        "accuracy_display",
        "beatmap",
        "result_display",
        "mutation_display",
    ]
    list_select_related = ["user_stats__user", "beatmap"]

    @admin.display(description="User")
    def user(self, obj: Score):
        return obj.user_stats.user

    @admin.display(description="Mods")
    def mods_display(self, obj: Score):
        if len(obj.mods_json) == 0:
            return None
        return utils.get_mods_string_from_json_mods(obj.mods_json)

    @admin.display(description="Accuracy")
    def accuracy_display(self, obj: Score):
        return f"{obj.accuracy:.2f}%"

    @admin.display(description="Result")
    def result_display(self, obj: Score):
        if obj.result == None:
            return None
        return ScoreResult(obj.result).name

    @admin.display(description="Mutation")
    def mutation_display(self, obj: Score):
        return ScoreMutation(obj.mutation).name


class PerformanceCalculationAdmin(admin.ModelAdmin):
    model = PerformanceCalculation
    raw_id_fields = (
        "score",
        "difficulty_calculation",
    )

    # no joins because it gets really slow, especially on high page numbers
    list_display = [
        "id",
        "score_id",
        "calculator_engine",
        "calculator_version",
    ]


class PerformanceValueAdmin(admin.ModelAdmin):
    model = PerformanceValue
    raw_id_fields = ("calculation",)

    list_display = [
        "id",
        "score_id_display",
        "calculator_engine_display",
        "calculator_version_display",
        "name",
        "value",
    ]
    list_select_related = ["calculation"]

    @admin.display(description="Score ID")
    def score_id_display(self, obj: PerformanceValue):
        return obj.calculation.score_id

    @admin.display(description="Calculator Engine")
    def calculator_engine_display(self, obj: PerformanceValue):
        return obj.calculation.calculator_engine

    @admin.display(description="Calculator Version")
    def calculator_version_display(self, obj: PerformanceValue):
        return obj.calculation.calculator_version


admin.site.register(OsuUser, OsuUserAdmin)
admin.site.register(UserStats, UserStatsAdmin)
admin.site.register(Beatmap, BeatmapAdmin)
admin.site.register(DifficultyCalculation, DifficultyCalculationAdmin)
admin.site.register(DifficultyValue, DifficultyValueAdmin)
admin.site.register(Score, ScoreAdmin)
admin.site.register(PerformanceCalculation, PerformanceCalculationAdmin)
admin.site.register(PerformanceValue, PerformanceValueAdmin)
admin.site.register(ScoreFilter)
