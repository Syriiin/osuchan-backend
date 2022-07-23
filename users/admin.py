from django.contrib import admin

from users.models import ScoreFilterPreset


class ScoreFilterPresetAdmin(admin.ModelAdmin):
    model = ScoreFilterPreset
    raw_id_fields = (
        "user",
        "score_filter",
    )


admin.site.register(ScoreFilterPreset, ScoreFilterPresetAdmin)
