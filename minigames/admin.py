from django.contrib import admin

from minigames.models import Minigame, MinigamePlayer, MinigameStats, MinigameTeam


class MinigameAdmin(admin.ModelAdmin):
    model = Minigame
    list_display = ["id", "name", "game_type", "status", "start_time", "end_time"]
    list_filter = ["game_type", "status"]
    search_fields = ["name"]


class MinigameTeamAdmin(admin.ModelAdmin):
    model = MinigameTeam
    list_display = ["id", "name", "minigame", "points", "score_count"]
    search_fields = ["name"]
    raw_id_fields = ["minigame"]


class MinigamePlayerAdmin(admin.ModelAdmin):
    model = MinigamePlayer
    list_display = ["id", "user", "team", "points", "score_count"]
    search_fields = ["user__username", "team__name"]
    raw_id_fields = ["user", "team"]


admin.site.register(Minigame, MinigameAdmin)
admin.site.register(MinigameTeam, MinigameTeamAdmin)
admin.site.register(MinigamePlayer, MinigamePlayerAdmin)
admin.site.register(MinigameStats)
