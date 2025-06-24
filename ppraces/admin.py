from django.contrib import admin

from ppraces.models import PPRace, PPRacePlayer, PPRaceTeam


class PPRaceAdmin(admin.ModelAdmin):
    model = PPRace
    list_display = ["id", "name", "start_time"]
    search_fields = ["name"]


class PPRaceTeamAdmin(admin.ModelAdmin):
    model = PPRaceTeam
    list_display = ["id", "name", "pprace", "total_pp", "score_count"]
    search_fields = ["name"]
    raw_id_fields = ["pprace"]


class PPRacePlayerAdmin(admin.ModelAdmin):
    model = PPRacePlayer
    list_display = ["id", "user", "team", "pp", "score_count"]
    search_fields = ["user__username", "team__name"]
    raw_id_fields = ["user", "team"]


admin.site.register(PPRace, PPRaceAdmin)
admin.site.register(PPRaceTeam, PPRaceTeamAdmin)
admin.site.register(PPRacePlayer, PPRacePlayerAdmin)
