from django.contrib.auth.models import AbstractUser
from django.db import models

from profiles.models import OsuUser


class User(AbstractUser):
    """
    Custom user model
    """

    id = models.BigAutoField(primary_key=True)

    is_beta_tester = models.BooleanField(default=False)

    # Relations
    osu_user = models.OneToOneField(
        OsuUser, on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        if self.osu_user:
            return "{} ({})".format(self.username, self.osu_user.username)
        else:
            return self.username
