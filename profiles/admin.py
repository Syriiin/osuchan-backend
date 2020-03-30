from django.contrib import admin

from profiles.models import OsuUser, UserStats, Beatmap, Score, ScoreFilter

admin.site.register(OsuUser)
admin.site.register(UserStats)
admin.site.register(Beatmap)
admin.site.register(Score)
admin.site.register(ScoreFilter)
