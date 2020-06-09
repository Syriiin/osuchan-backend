from rest_framework import serializers

from osuauth.models import User, ScoreFilterPreset
from profiles.serialisers import OsuUserSerialiser, ScoreFilterSerialiser

class UserSerialiser(serializers.ModelSerializer):
    osu_user = OsuUserSerialiser()

    class Meta:
        model = User
        fields = (
            "id",
            "date_joined",
            "is_beta_tester",
            # relations
            "osu_user"
        )

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
