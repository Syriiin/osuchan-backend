from rest_framework import serializers

from profiles.serialisers import ScoreFilterSerialiser
from users.models import ScoreFilterPreset


class ScoreFilterPresetSerialiser(serializers.ModelSerializer):
    score_filter = ScoreFilterSerialiser()

    class Meta:
        model = ScoreFilterPreset
        fields = (
            "id",
            "name",
            # relations
            "user",
            "score_filter",
        )
