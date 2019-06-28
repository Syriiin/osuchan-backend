from django.contrib import admin

from leaderboards.models import Leaderboard, Membership

admin.site.register(Leaderboard)
admin.site.register(Membership)
