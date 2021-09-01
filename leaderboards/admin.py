from django.contrib import admin

from leaderboards.models import Invite, Leaderboard, Membership

admin.site.register(Leaderboard)
admin.site.register(Membership)
admin.site.register(Invite)
