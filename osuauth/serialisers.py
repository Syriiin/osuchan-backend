from rest_framework import serializers

from osuauth.models import User
from profiles.serialisers import OsuUserSerialiser


class UserSerialiser(serializers.ModelSerializer):
    osu_user = OsuUserSerialiser()

    class Meta:
        model = User
        fields = (
            "id",
            "date_joined",
            "is_beta_tester",
            # relations
            "osu_user",
        )
