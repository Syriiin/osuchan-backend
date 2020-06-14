from rest_framework import serializers

from users.models import ScoreFilterPreset
from profiles.serialisers import ScoreFilterSerialiser

class ScoreFilterPresetSerialiser(serializers.ModelSerializer):
    score_filter = ScoreFilterSerialiser()

    class Meta:
        model = ScoreFilterPreset
        fields = (
            "id",
            "name",
            # relations
            "user",
            "score_filter"
        )
