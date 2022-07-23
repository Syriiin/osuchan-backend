from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from osuauth.models import User


class UserAdmin(BaseUserAdmin):
    """
    Custom user admin
    """

    list_display = ("username", "osu_user", "is_staff")
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "is_beta_tester",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
        ("osu! user", {"fields": ("osu_user",)}),
    )
    raw_id_fields = ("osu_user",)

    # NOTE: there seems to be some odd error when editing this class from __init__ which means we cant add to members:
    #   django.core.exceptions.ImproperlyConfigured: AUTH_USER_MODEL refers to model 'osuauth.User' that has not been installed
    #   perhaps this is caused by us setting a custom user which gets used before the app is installed?
    #   not entirely sure, but it means i we have to copy+paste the members if we want the defaults


admin.site.register(User, UserAdmin)
