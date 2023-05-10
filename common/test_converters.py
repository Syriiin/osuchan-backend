from unittest import TestCase

from common.converters import GamemodeConverter, LeaderboardTypeConverter
from common.osu.enums import Gamemode


class UtilsTestCase(TestCase):
    def setUp(self) -> None:
        self.converter = GamemodeConverter()

    def test_to_python(self):
        self.assertEqual(self.converter.to_python("osu"), Gamemode.STANDARD)
        self.assertEqual(self.converter.to_python("taiko"), Gamemode.TAIKO)
        self.assertEqual(self.converter.to_python("catch"), Gamemode.CATCH)
        self.assertEqual(self.converter.to_python("mania"), Gamemode.MANIA)

    def test_to_url(self):
        self.assertEqual(self.converter.to_url(Gamemode.STANDARD), "osu")
        self.assertEqual(self.converter.to_url(Gamemode.TAIKO), "taiko")
        self.assertEqual(self.converter.to_url(Gamemode.CATCH), "catch")
        self.assertEqual(self.converter.to_url(Gamemode.MANIA), "mania")


class LeaderboardTypeConverterTestCase(TestCase):
    def setUp(self) -> None:
        self.converter = LeaderboardTypeConverter()

    def test_to_python(self):
        self.assertEqual(self.converter.to_python("global"), "global")

    def test_to_url(self):
        self.assertEqual(self.converter.to_url("global"), "global")
