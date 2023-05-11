from unittest import TestCase

from common.osu.enums import Gamemode, Mods
from common.osu.utils import (
    calculate_pp_total,
    get_accuracy,
    get_ar,
    get_bpm,
    get_cs,
    get_gamemode_from_gamemode_string,
    get_gamemode_string_from_gamemode,
    get_length,
    get_mods_string,
    get_od,
)


class UtilsTestCase(TestCase):
    def test_calculate_pp_total(self):
        pp_values = [1322, 1260, 1158, 1023, 900, 800, 727, 603, 541, 408]
        self.assertEqual(calculate_pp_total(pp_values), 7364.83140652393)

    def test_get_accuracy(self):
        self.assertEqual(
            get_accuracy(
                count_300=1739,
                count_100=14,
                count_50=0,
                count_miss=0,
                gamemode=Gamemode.STANDARD,
            ),
            99.4675793877163,
        )
        self.assertEqual(
            get_accuracy(
                count_300=2950,
                count_100=14,
                count_50=0,
                count_miss=0,
                gamemode=Gamemode.TAIKO,
            ),
            99.7638326585695,
        )
        self.assertEqual(
            get_accuracy(
                count_300=4431,
                count_100=109,
                count_50=0,
                count_miss=0,
                count_katu=2,
                gamemode=Gamemode.CATCH,
            ),
            99.95596653456627,
        )
        self.assertEqual(
            get_accuracy(
                count_300=2724,
                count_100=26,
                count_50=17,
                count_miss=37,
                count_katu=171,
                count_geki=7853,
                gamemode=Gamemode.MANIA,
            ),
            98.84096786110085,
        )

    def test_get_bpm(self):
        self.assertEqual(get_bpm(180, Mods.NONE), 180)
        self.assertEqual(get_bpm(180, Mods.DOUBLETIME), 270)
        self.assertEqual(get_bpm(180, Mods.DOUBLETIME + Mods.NIGHTCORE), 270)
        self.assertEqual(get_bpm(180, Mods.HALFTIME), 135)

    def test_get_length(self):
        self.assertEqual(get_length(90, Mods.NONE), 90)
        self.assertEqual(get_length(90, Mods.DOUBLETIME), 60)
        self.assertEqual(get_length(90, Mods.DOUBLETIME + Mods.NIGHTCORE), 60)
        self.assertEqual(get_length(90, Mods.HALFTIME), 120)

    def test_get_cs(self):
        self.assertEqual(get_cs(4, Mods.NONE, Gamemode.STANDARD), 4)
        self.assertEqual(get_cs(4, Mods.HARDROCK, Gamemode.STANDARD), 5.2)
        self.assertEqual(get_cs(4, Mods.EASY, Gamemode.STANDARD), 2)
        self.assertEqual(get_cs(4, Mods.KEY_1, Gamemode.MANIA), 1)

    def test_get_ar(self):
        self.assertEqual(get_ar(9, Mods.NONE), 9)
        self.assertEqual(get_ar(9, Mods.DOUBLETIME), 10.333333333333334)
        self.assertEqual(
            get_ar(9, Mods.DOUBLETIME + Mods.NIGHTCORE), 10.333333333333334
        )
        self.assertEqual(get_ar(9, Mods.HARDROCK), 10)
        self.assertEqual(get_ar(9, Mods.HALFTIME), 7.666666666666667)
        self.assertEqual(get_ar(9, Mods.EASY), 4.5)

    def test_get_od(self):
        self.assertEqual(get_od(9, Mods.NONE), 9)
        self.assertEqual(get_od(9, Mods.DOUBLETIME), 10.416666666666666)
        self.assertEqual(
            get_od(9, Mods.DOUBLETIME + Mods.NIGHTCORE), 10.416666666666666
        )
        self.assertEqual(get_od(9, Mods.HARDROCK), 10)
        self.assertEqual(get_od(9, Mods.HALFTIME), 7.583333333333333)
        self.assertEqual(get_od(9, Mods.EASY), 4.5)

    def test_get_gamemode_from_gamemode_string(self):
        self.assertEqual(get_gamemode_from_gamemode_string("osu"), Gamemode.STANDARD)
        self.assertEqual(get_gamemode_from_gamemode_string("taiko"), Gamemode.TAIKO)
        self.assertEqual(get_gamemode_from_gamemode_string("catch"), Gamemode.CATCH)
        self.assertEqual(get_gamemode_from_gamemode_string("mania"), Gamemode.MANIA)

    def test_get_gamemode_string_from_gamemode(self):
        self.assertEqual(get_gamemode_string_from_gamemode(Gamemode.STANDARD), "osu")
        self.assertEqual(get_gamemode_string_from_gamemode(Gamemode.TAIKO), "taiko")
        self.assertEqual(get_gamemode_string_from_gamemode(Gamemode.CATCH), "catch")
        self.assertEqual(get_gamemode_string_from_gamemode(Gamemode.MANIA), "mania")

    def test_get_mods_string(self):
        self.assertEqual(
            get_mods_string(Mods.HIDDEN + Mods.DOUBLETIME + Mods.SUDDEN_DEATH),
            "HD,SD,DT",
        )