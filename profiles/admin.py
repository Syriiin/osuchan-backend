from django.contrib import admin

from profiles.models import Beatmap, OsuUser, Score, ScoreFilter, UserStats


class UserStatsAdmin(admin.ModelAdmin):
    model = UserStats
    raw_id_fields = ("user",)


class BeatmapAdmin(admin.ModelAdmin):
    model = Beatmap
    raw_id_fields = ("creator",)


class ScoreAdmin(admin.ModelAdmin):
    model = Score
    raw_id_fields = (
        "beatmap",
        "user_stats",
    )


admin.site.register(OsuUser)
admin.site.register(UserStats, UserStatsAdmin)
admin.site.register(Beatmap, BeatmapAdmin)
admin.site.register(Score, ScoreAdmin)
admin.site.register(ScoreFilter)
