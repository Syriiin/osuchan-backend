from django.contrib import admin

from events.models import (
    BeatmapChallenge,
    BeatmapChallengeScore,
    Event,
    EventAttendee,
    EventLeaderboard,
    EventOrganiser,
    EventStats,
)


class EventAdmin(admin.ModelAdmin):
    model = Event
    prepopulated_fields = {"slug": ("name",)}
    list_display = [
        "__str__",
        "slug",
        "start_date",
        "end_date",
    ]


class EventOrganiserAdmin(admin.ModelAdmin):
    model = EventOrganiser
    raw_id_fields = ("event", "user")

    list_display = [
        "id",
        "event",
        "user",
    ]


class EventAttendeeAdmin(admin.ModelAdmin):
    model = EventAttendee
    raw_id_fields = ("event", "user")

    list_display = [
        "id",
        "event",
        "user",
    ]


class EventLeaderboardAdmin(admin.ModelAdmin):
    model = EventLeaderboard
    raw_id_fields = ("event", "leaderboard")

    list_display = [
        "id",
        "event",
        "leaderboard",
    ]


class EventStatsAdmin(admin.ModelAdmin):
    model = EventStats
    raw_id_fields = ("event",)

    list_display = [
        "id",
        "event",
        "total_scores",
        "total_play_time",
        "total_pp",
        "unique_players",
        "last_updated",
    ]


class BeatmapChallengeAdmin(admin.ModelAdmin):
    model = BeatmapChallenge
    raw_id_fields = ("event", "beatmap")

    list_display = [
        "__str__",
        "event_id",
        "challenge_type",
    ]


class BeatmapChallengeScoreAdmin(admin.ModelAdmin):
    model = BeatmapChallengeScore
    raw_id_fields = ("challenge", "score")

    list_display = [
        "id",
        "challenge_id",
        "score_id",
        "user_id",
    ]


admin.site.register(Event, EventAdmin)
admin.site.register(EventOrganiser, EventOrganiserAdmin)
admin.site.register(EventAttendee, EventAttendeeAdmin)
admin.site.register(EventLeaderboard, EventLeaderboardAdmin)
admin.site.register(EventStats, EventStatsAdmin)
admin.site.register(BeatmapChallenge, BeatmapChallengeAdmin)
admin.site.register(BeatmapChallengeScore, BeatmapChallengeScoreAdmin)
