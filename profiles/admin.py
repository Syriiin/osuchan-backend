from django.contrib import admin

from profiles.models import Beatmap, OsuUser, Score, ScoreFilter, UserStats

admin.site.register(OsuUser)
admin.site.register(UserStats)
admin.site.register(Beatmap)
admin.site.register(Score)
admin.site.register(ScoreFilter)
