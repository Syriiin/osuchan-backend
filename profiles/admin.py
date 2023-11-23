from django.contrib import admin

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


class UserStatsAdmin(admin.ModelAdmin):
    model = UserStats
    raw_id_fields = ("user",)


class BeatmapAdmin(admin.ModelAdmin):
    model = Beatmap
    raw_id_fields = ("creator",)


class DifficultyCalculationAdmin(admin.ModelAdmin):
    model = DifficultyCalculation
    raw_id_fields = ("beatmap",)


class DifficultyValueAdmin(admin.ModelAdmin):
    model = DifficultyCalculation
    raw_id_fields = ("calculation",)


class ScoreAdmin(admin.ModelAdmin):
    model = Score
    raw_id_fields = (
        "beatmap",
        "user_stats",
    )


class PerformanceCalculationAdmin(admin.ModelAdmin):
    model = PerformanceCalculation
    raw_id_fields = (
        "score",
        "difficulty_calculation",
    )


class PerformanceValueAdmin(admin.ModelAdmin):
    model = PerformanceCalculation
    raw_id_fields = ("calculation",)


admin.site.register(OsuUser)
admin.site.register(UserStats, UserStatsAdmin)
admin.site.register(Beatmap, BeatmapAdmin)
admin.site.register(DifficultyCalculation, DifficultyCalculationAdmin)
admin.site.register(DifficultyValue, DifficultyValueAdmin)
admin.site.register(Score, ScoreAdmin)
admin.site.register(PerformanceCalculation, PerformanceCalculationAdmin)
admin.site.register(PerformanceValue, PerformanceValueAdmin)
admin.site.register(ScoreFilter)
