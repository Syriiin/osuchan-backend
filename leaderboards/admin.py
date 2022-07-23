from django.contrib import admin

from leaderboards.models import Invite, Leaderboard, Membership


class LeaderboardAdmin(admin.ModelAdmin):
    model = Leaderboard
    raw_id_fields = (
        "owner",
        "score_filter",
    )


class MembershipAdmin(admin.ModelAdmin):
    model = Membership
    filter_horizontal = ("scores",)
    raw_id_fields = ("leaderboard", "user", "scores")


class InviteAdmin(admin.ModelAdmin):
    model = Invite
    raw_id_fields = (
        "leaderboard",
        "user",
    )


admin.site.register(Leaderboard, LeaderboardAdmin)
admin.site.register(Membership, MembershipAdmin)
admin.site.register(Invite, InviteAdmin)
