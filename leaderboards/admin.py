from django.contrib import admin

from common.osu.enums import Gamemode
from leaderboards.enums import LeaderboardAccessType
from leaderboards.models import Invite, Leaderboard, Membership


class LeaderboardAdmin(admin.ModelAdmin):
    model = Leaderboard
    raw_id_fields = (
        "owner",
        "score_filter",
    )

    list_display = [
        "__str__",
        "gamemode_display",
        "access_type_display",
        "member_count",
        "archived",
        "owner",
        "creation_time",
    ]
    list_select_related = ["owner"]
    list_filter = ["gamemode", "access_type", "archived"]

    @admin.display(description="Gamemode")
    def gamemode_display(self, obj: Leaderboard):
        return Gamemode(obj.gamemode).name

    @admin.display(description="Access Type")
    def access_type_display(self, obj: Leaderboard):
        return LeaderboardAccessType(obj.access_type).name


class MembershipAdmin(admin.ModelAdmin):
    model = Membership
    raw_id_fields = ("leaderboard", "user")

    list_display = [
        "id",
        "leaderboard",
        "user",
        "pp",
        "rank",
        "score_count",
    ]


class InviteAdmin(admin.ModelAdmin):
    model = Invite
    raw_id_fields = (
        "leaderboard",
        "user",
    )

    list_display = [
        "id",
        "leaderboard",
        "user",
        "invite_date",
    ]


admin.site.register(Leaderboard, LeaderboardAdmin)
admin.site.register(Membership, MembershipAdmin)
admin.site.register(Invite, InviteAdmin)
