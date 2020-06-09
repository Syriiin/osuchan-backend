from django.db import models
from django.contrib.auth.models import AbstractUser

from profiles.models import OsuUser, ScoreFilter

class User(AbstractUser):
    """
    Custom user model
    """
    
    is_beta_tester = models.BooleanField(default=False)

    # Relations
    osu_user = models.OneToOneField(OsuUser, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        if self.osu_user:
            return "{} ({})".format(self.username, self.osu_user.username)
        else:
            return self.username

class ScoreFilterPreset(models.Model):
    name = models.CharField(max_length=30)

    # Relations
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score_filter = models.ForeignKey(ScoreFilter, on_delete=models.CASCADE)
