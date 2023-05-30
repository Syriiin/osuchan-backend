import pytest

from osuauth.models import User
from profiles.models import OsuUser


@pytest.mark.django_db
class TestUser:
    @pytest.fixture
    def user_with_osu_user(self, user: User, osu_user: OsuUser):
        user.osu_user = osu_user
        user.save()
        return user

    def test_magic_str(self, user: User):
        assert str(user) == "testusername"

    def test_magic_str_with_osu_user(self, user_with_osu_user: User):
        assert str(user_with_osu_user) == "testusername (TestOsuUser)"
