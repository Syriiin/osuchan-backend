import pytest

from common.converters import GamemodeConverter, LeaderboardTypeConverter
from common.osu.enums import Gamemode


class TestConverters:
    @pytest.fixture
    def converter(self):
        return GamemodeConverter()

    def test_to_python(self, converter: GamemodeConverter):
        assert converter.to_python("osu") == Gamemode.STANDARD
        assert converter.to_python("taiko") == Gamemode.TAIKO
        assert converter.to_python("catch") == Gamemode.CATCH
        assert converter.to_python("mania") == Gamemode.MANIA

    def test_to_url(self, converter: GamemodeConverter):
        assert converter.to_url(Gamemode.STANDARD) == "osu"
        assert converter.to_url(Gamemode.TAIKO) == "taiko"
        assert converter.to_url(Gamemode.CATCH) == "catch"
        assert converter.to_url(Gamemode.MANIA) == "mania"


class LeaderboardTypeConverterTestCase:
    @pytest.fixture
    def converter(self):
        return LeaderboardTypeConverter()

    def test_to_python(self, converter: LeaderboardTypeConverter):
        assert converter.to_python("global") == "global"

    def test_to_url(self, converter: LeaderboardTypeConverter):
        assert converter.to_url("global") == "global"
