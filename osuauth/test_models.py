import pytest

from osuauth.models import User
from profiles.models import OsuUser


class TestUser:
    @pytest.fixture
    def user(self):
        return User(id=1, username="testusername")

    @pytest.fixture
    def user_with_osu_user(self, user):
        user.osu_user = OsuUser(username="TestOsuUsername")
        return user

    def test_magic_str(self, user: User):
        assert str(user) == "testusername"

    def test_magic_str_with_osu_user(self, user_with_osu_user: User):
        assert str(user_with_osu_user) == "testusername (TestOsuUsername)"
