from django.db import models

from osuauth.models import User
from profiles.models import ScoreFilter

class ScoreFilterPreset(models.Model):
    name = models.CharField(max_length=30)

    # Relations
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score_filter = models.ForeignKey(ScoreFilter, on_delete=models.CASCADE)
