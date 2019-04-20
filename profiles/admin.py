from django.contrib import admin

from profiles.models import OsuUser, UserStats, Beatmap, Score

admin.site.register(OsuUser)
admin.site.register(UserStats)
admin.site.register(Beatmap)
admin.site.register(Score)
