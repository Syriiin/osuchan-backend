from django.contrib import admin

from users.models import ScoreFilterPreset


class ScoreFilterPresetAdmin(admin.ModelAdmin):
    model = ScoreFilterPreset
    raw_id_fields = (
        "user",
        "score_filter",
    )

    list_display = [
        "__str__",
        "user",
    ]
    list_select_related = ["user__osu_user"]


admin.site.register(ScoreFilterPreset, ScoreFilterPresetAdmin)
