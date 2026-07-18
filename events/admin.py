from django.contrib import admin

from events.models import Event, EventAttendee, EventLeaderboard, EventOrganiser


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


admin.site.register(Event, EventAdmin)
admin.site.register(EventOrganiser, EventOrganiserAdmin)
admin.site.register(EventAttendee, EventAttendeeAdmin)
admin.site.register(EventLeaderboard, EventLeaderboardAdmin)
