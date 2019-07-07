from django.contrib import admin

from leaderboards.models import Leaderboard, Membership, Invite

admin.site.register(Leaderboard)
admin.site.register(Membership)
admin.site.register(Invite)
