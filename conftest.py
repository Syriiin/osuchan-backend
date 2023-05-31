from datetime import datetime, timezone

import pytest

from common.osu.enums import Mods
from osuauth.models import User
from profiles.models import OsuUser, ScoreFilter


@pytest.fixture
def user():
    return User.objects.create(username="testusername")


@pytest.fixture
def osu_user():
    return OsuUser.objects.create(
        id=1,
        username="TestOsuUser",
        country="au",
        join_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
        disabled=False,
    )


@pytest.fixture
def score_filter():
    return ScoreFilter.objects.create(required_mods=Mods.HIDDEN)
