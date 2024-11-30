from common.osu.enums import Gamemode, Mods
from common.osu.utils import (
    calculate_pp_total,
    get_ar,
    get_bitwise_mods,
    get_bpm,
    get_classic_accuracy,
    get_cs,
    get_gamemode_from_gamemode_string,
    get_gamemode_string_from_gamemode,
    get_json_mods,
    get_length,
    get_mods_string,
    get_od,
)


def test_calculate_pp_total():
    pp_values = [1322, 1260, 1158, 1023, 900, 800, 727, 603, 541, 408]
    assert calculate_pp_total(pp_values) == 7364.831406523928


def test_get_accuracy():
    assert (
        get_classic_accuracy(
            statistics={
                "great": 1739,
                "ok": 14,
                "meh": 0,
                "miss": 0,
            },
            gamemode=Gamemode.STANDARD,
        )
        == 99.4675793877163
    )
    assert (
        get_classic_accuracy(
            statistics={
                "great": 2950,
                "ok": 14,
                "miss": 0,
            },
            gamemode=Gamemode.TAIKO,
        )
        == 99.7638326585695
    )
    assert (
        get_classic_accuracy(
            statistics={
                "great": 4431,
                "large_tick_hit": 109,
                "small_tick_hit": 0,
                "miss": 0,
                "small_tick_miss": 2,
            },
            gamemode=Gamemode.CATCH,
        )
        == 99.95596653456627
    )
    assert (
        get_classic_accuracy(
            statistics={
                "perfect": 7853,
                "great": 2724,
                "good": 171,
                "ok": 26,
                "meh": 17,
                "miss": 37,
            },
            gamemode=Gamemode.MANIA,
        )
        == 98.84096786110085
    )


def test_get_bpm():
    assert get_bpm(180, Mods.NONE) == 180
    assert get_bpm(180, Mods.DOUBLETIME) == 270
    assert get_bpm(180, Mods.DOUBLETIME + Mods.NIGHTCORE) == 270
    assert get_bpm(180, Mods.HALFTIME) == 135


def test_get_length():
    assert get_length(90, Mods.NONE) == 90
    assert get_length(90, Mods.DOUBLETIME) == 60
    assert get_length(90, Mods.DOUBLETIME + Mods.NIGHTCORE) == 60
    assert get_length(90, Mods.HALFTIME) == 120


def test_get_cs():
    assert get_cs(4, Mods.NONE, Gamemode.STANDARD) == 4
    assert get_cs(4, Mods.HARDROCK, Gamemode.STANDARD) == 5.2
    assert get_cs(4, Mods.EASY, Gamemode.STANDARD) == 2
    assert get_cs(4, Mods.KEY_1, Gamemode.MANIA) == 1
    assert get_cs(4, Mods.KEY_2, Gamemode.MANIA) == 2
    assert get_cs(4, Mods.KEY_3, Gamemode.MANIA) == 3
    assert get_cs(4, Mods.KEY_4, Gamemode.MANIA) == 4
    assert get_cs(4, Mods.KEY_5, Gamemode.MANIA) == 5
    assert get_cs(4, Mods.KEY_6, Gamemode.MANIA) == 6
    assert get_cs(4, Mods.KEY_7, Gamemode.MANIA) == 7
    assert get_cs(4, Mods.KEY_8, Gamemode.MANIA) == 8
    assert get_cs(4, Mods.KEY_9, Gamemode.MANIA) == 9
    assert get_cs(4, Mods.KEY_COOP, Gamemode.MANIA) == 4


def test_get_ar():
    assert get_ar(9, Mods.NONE) == 9
    assert get_ar(9, Mods.DOUBLETIME) == 10.333333333333334
    assert get_ar(9, Mods.DOUBLETIME + Mods.NIGHTCORE) == 10.333333333333334
    assert get_ar(9, Mods.HARDROCK) == 10

    assert get_ar(5, Mods.HALFTIME) == 1.6666666666666667
    assert get_ar(5, Mods.EASY) == 2.5


def test_get_od():
    assert get_od(9, Mods.NONE) == 9
    assert get_od(9, Mods.DOUBLETIME) == 10.416666666666666
    assert get_od(9, Mods.DOUBLETIME + Mods.NIGHTCORE) == 10.416666666666666
    assert get_od(9, Mods.HARDROCK) == 10

    assert get_od(5, Mods.HALFTIME) == 2.25
    assert get_od(5, Mods.EASY) == 2.5


def test_get_gamemode_from_gamemode_string():
    assert get_gamemode_from_gamemode_string("osu") == Gamemode.STANDARD
    assert get_gamemode_from_gamemode_string("taiko") == Gamemode.TAIKO
    assert get_gamemode_from_gamemode_string("catch") == Gamemode.CATCH
    assert get_gamemode_from_gamemode_string("mania") == Gamemode.MANIA


def test_get_gamemode_string_from_gamemode():
    assert get_gamemode_string_from_gamemode(Gamemode.STANDARD) == "osu"
    assert get_gamemode_string_from_gamemode(Gamemode.TAIKO) == "taiko"
    assert get_gamemode_string_from_gamemode(Gamemode.CATCH) == "catch"
    assert get_gamemode_string_from_gamemode(Gamemode.MANIA) == "mania"


def test_get_mods_string():
    assert (
        get_mods_string(Mods.HIDDEN + Mods.DOUBLETIME + Mods.SUDDEN_DEATH) == "HD,SD,DT"
    )


def test_get_json_mods():
    assert get_json_mods(Mods.HIDDEN + Mods.SUDDEN_DEATH + Mods.DOUBLETIME, True) == [
        {"acronym": "HD"},
        {"acronym": "SD"},
        {"acronym": "DT"},
        {"acronym": "CL"},
    ]

    assert get_json_mods(
        Mods.HARDROCK
        + Mods.FLASHLIGHT
        + Mods.SUDDEN_DEATH
        + Mods.PERFECT
        + Mods.DOUBLETIME
        + Mods.NIGHTCORE,
        False,
    ) == [
        {"acronym": "HR"},
        {"acronym": "NC"},
        {"acronym": "FL"},
        {"acronym": "PF"},
    ]


def test_get_bitwise_mods():
    assert (
        get_bitwise_mods(["HD", "DT", "SD", "CL"])
        == Mods.HIDDEN + Mods.SUDDEN_DEATH + Mods.DOUBLETIME
    )
    assert (
        get_bitwise_mods(["HR", "FL", "PF", "NC"])
        == Mods.HARDROCK
        + Mods.FLASHLIGHT
        + Mods.SUDDEN_DEATH
        + Mods.PERFECT
        + Mods.DOUBLETIME
        + Mods.NIGHTCORE
    )
