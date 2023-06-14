import pytest

from osuauth.models import User


@pytest.mark.django_db
class TestUser:
    @pytest.fixture
    def user_without_osu_user(self):
        return User.objects.create(username="testusername")

    def test_magic_str(self, user_without_osu_user: User):
        assert str(user_without_osu_user) == "testusername"

    def test_magic_str_with_osu_user(self, user: User):
        assert str(user) == "1 (TestOsuUser)"
