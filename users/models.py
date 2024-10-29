from django.db import models

from osuauth.models import User
from profiles.models import ScoreFilter


class ScoreFilterPreset(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField()

    # Relations
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score_filter = models.ForeignKey(ScoreFilter, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
