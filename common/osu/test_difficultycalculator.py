import pytest

from common.osu.difficultycalculator import (
    BeatmapDetails,
    Calculation,
    CalculationException,
    DifficalcyCatchDifficultyCalculator,
    DifficalcyManiaDifficultyCalculator,
    DifficalcyOsuDifficultyCalculator,
    DifficalcyPerformancePlusDifficultyCalculator,
    DifficalcyTaikoDifficultyCalculator,
    Score,
)
from common.osu.enums import NewMods


class TestDifficalcyDifficultyCalculator:
    def test_context_manager(self):
        with DifficalcyOsuDifficultyCalculator() as calc:
            assert calc.calculate_scores(
                [Score("307618", mods={NewMods.CLASSIC: {}})]
            ) == [
                Calculation(
                    difficulty_values={
                        "aim": 2.118735459664974,
                        "speed": 2.1684114250452144,
                        "flashlight": 0,
                        "total": 4.492310309756154,
                    },
                    performance_values={
                        "aim": 46.26971335416548,
                        "speed": 49.870242023878504,
                        "accuracy": 36.07670429437059,
                        "flashlight": 0,
                        "total": 137.7209357109564,
                    },
                )
            ]

    def test_invalid_beatmap(self):
        with pytest.raises(CalculationException):
            with DifficalcyOsuDifficultyCalculator() as calc:
                calc.calculate_scores([Score("notarealbeatmap")])

    def test_calculate_scores(self):
        calc = DifficalcyOsuDifficultyCalculator()
        scores = [
            Score(
                "307618",
                mods={NewMods.DOUBLETIME: {}, NewMods.HIDDEN: {}, NewMods.CLASSIC: {}},
                statistics={
                    "ok": 14,
                    "meh": 1,
                    "miss": 1,
                },
                combo=2000,
            ),
            Score(
                "307618",
                mods={
                    NewMods.DOUBLETIME: {},
                    NewMods.HIDDEN: {},
                    NewMods.HARDROCK: {},
                    NewMods.CLASSIC: {},
                },
                statistics={
                    "ok": 14,
                    "meh": 1,
                    "miss": 1,
                },
                combo=2000,
            ),
            Score(
                "307618",
                mods={
                    NewMods.DOUBLETIME: {},
                    NewMods.HIDDEN: {},
                    NewMods.HARDROCK: {},
                    NewMods.CLASSIC: {},
                },
            ),
            Score(
                "422328",
                statistics={
                    "ok": 13,
                    "miss": 14,
                    "great": 333,
                    "ignore_hit": 1,
                    "ignore_miss": 8,
                    "large_bonus": 3,
                    "small_bonus": 21,
                    "large_tick_hit": 26,
                    "slider_tail_hit": 1,
                },
                combo=127,
            ),
        ]
        assert calc.calculate_scores(scores) == [
            Calculation(
                difficulty_values={
                    "aim": 2.931964039669495,
                    "speed": 3.0719986654662823,
                    "flashlight": 0,
                    "total": 6.294293342707777,
                },
                performance_values={
                    "aim": 122.84647751158279,
                    "speed": 137.46274757505594,
                    "accuracy": 84.96884392557897,
                    "flashlight": 0,
                    "total": 360.0168757722653,
                },
            ),
            Calculation(
                difficulty_values={
                    "aim": 3.1710525152307567,
                    "speed": 3.0845312684219364,
                    "flashlight": 0,
                    "total": 6.55537654432227,
                },
                performance_values={
                    "aim": 188.94497690504716,
                    "speed": 176.4711288544247,
                    "accuracy": 166.32370945374015,
                    "flashlight": 0,
                    "total": 553.4538750505777,
                },
            ),
            Calculation(
                difficulty_values={
                    "aim": 3.1710525152307567,
                    "speed": 3.0845312684219364,
                    "flashlight": 0,
                    "total": 6.55537654432227,
                },
                performance_values={
                    "aim": 214.2988937175237,
                    "speed": 209.3293065089824,
                    "accuracy": 212.8087296294707,
                    "flashlight": 0,
                    "total": 662.3394875629771,
                },
            ),
            Calculation(
                difficulty_values={
                    "aim": 3.2556879022731793,
                    "speed": 2.0082542040175957,
                    "flashlight": 0,
                    "total": 5.854140027184703,
                },
                performance_values={
                    "aim": 49.7362338663849,
                    "speed": 7.181140914853874,
                    "accuracy": 12.368997155942548,
                    "flashlight": 0,
                    "total": 74.39650328828102,
                },
            ),
        ]


class TestDifficalcyOsuDifficultyCalculator:
    def test_enigne(self):
        assert DifficalcyOsuDifficultyCalculator.engine() == "osu.Game.Rulesets.Osu"

    def test_version(self):
        assert DifficalcyOsuDifficultyCalculator.version() == "2025.403.0.0"

    def test_calculate_scores(self):
        calc = DifficalcyOsuDifficultyCalculator()
        score = Score(
            "307618",
            mods={NewMods.DOUBLETIME: {}, NewMods.HIDDEN: {}, NewMods.CLASSIC: {}},
            statistics={
                "ok": 14,
                "meh": 1,
                "miss": 1,
            },
            combo=2000,
        )
        assert calc.calculate_scores([score]) == [
            Calculation(
                difficulty_values={
                    "aim": 2.931964039669495,
                    "speed": 3.0719986654662823,
                    "flashlight": 0,
                    "total": 6.294293342707777,
                },
                performance_values={
                    "aim": 122.84647751158279,
                    "speed": 137.46274757505594,
                    "accuracy": 84.96884392557897,
                    "flashlight": 0,
                    "total": 360.0168757722653,
                },
            )
        ]

    def test_get_beatmap_details(self):
        calc = DifficalcyOsuDifficultyCalculator()
        assert calc.get_beatmap_details("307618") == BeatmapDetails(
            hitobject_counts={
                "circles": 1093,
                "sliders": 659,
                "spinners": 1,
                "slider_ticks": 346,
            },
            difficulty_settings={
                "circle_size": 4,
                "approach_rate": 8,
                "accuracy": 6,
                "drain_rate": 5,
            },
            artist="senya",
            title="Songs Compilation",
            difficulty_name="Marathon",
            author="Satellite",
            max_combo=2758,
            length=678047,
            mininum_bpm=121,
            maximum_bpm=168,
            common_bpm=138,
            base_velocity=1.7,
            tick_rate=2,
        )


class TestDifficalcyTaikoDifficultyCalculator:
    def test_enigne(self):
        assert DifficalcyTaikoDifficultyCalculator.engine() == "osu.Game.Rulesets.Taiko"

    def test_version(self):
        assert DifficalcyTaikoDifficultyCalculator.version() == "2025.403.0.0"

    def test_calculate_scores(self):
        calc = DifficalcyTaikoDifficultyCalculator()
        score = Score(
            "2",
            mods={NewMods.DOUBLETIME: {}, NewMods.HARDROCK: {}, NewMods.CLASSIC: {}},
            statistics={
                "ok": 3,
                "miss": 5,
            },
            combo=150,
        )
        assert calc.calculate_scores([score]) == [
            Calculation(
                difficulty_values={
                    "stamina": 2.861677137388462,
                    "rhythm": 0.041069998580020146,
                    "colour": 0.6552532719640201,
                    "total": 4.616848744998109,
                },
                performance_values={
                    "difficulty": 89.17971591503598,
                    "accuracy": 159.13604655564944,
                    "total": 264.5185204474163,
                },
            )
        ]

    def test_get_beatmap_details(self):
        calc = DifficalcyTaikoDifficultyCalculator()
        assert calc.get_beatmap_details("2") == BeatmapDetails(
            hitobject_counts={"hits": 200, "drum_rolls": 30, "swells": 8},
            difficulty_settings={"accuracy": 7, "drain_rate": 5},
            artist="Unknown",
            title="Unknown",
            difficulty_name="Normal",
            author="Unknown Creator",
            max_combo=200,
            length=53000,
            mininum_bpm=120,
            maximum_bpm=120,
            common_bpm=120,
            base_velocity=1.6,
            tick_rate=1,
        )


class TestDifficalcyCatchDifficultyCalculator:
    def test_enigne(self):
        assert DifficalcyCatchDifficultyCalculator.engine() == "osu.Game.Rulesets.Catch"

    def test_version(self):
        assert DifficalcyCatchDifficultyCalculator.version() == "2025.403.0.0"

    def test_calculate_scores(self):
        calc = DifficalcyCatchDifficultyCalculator()
        score = Score(
            "3",
            mods={NewMods.DOUBLETIME: {}, NewMods.HARDROCK: {}, NewMods.CLASSIC: {}},
            statistics={
                "large_tick_hit": 18,
                "small_tick_hit": 200,
                "miss": 5,
            },
            combo=100,
        )
        assert calc.calculate_scores([score]) == [
            Calculation(
                difficulty_values={"total": 5.560488609256414},
                performance_values={"total": 226.4106426420045},
            )
        ]

    def test_get_beatmap_details(self):
        calc = DifficalcyCatchDifficultyCalculator()
        assert calc.get_beatmap_details("3") == BeatmapDetails(
            hitobject_counts={"fruits": 78, "juice_streams": 12, "banana_showers": 3},
            difficulty_settings={
                "circle_size": 4,
                "approach_rate": 8.3,
                "drain_rate": 5,
            },
            artist="Unknown",
            title="Unknown",
            difficulty_name="Normal",
            author="Unknown Creator",
            max_combo=127,
            length=45250,
            mininum_bpm=120,
            maximum_bpm=120,
            common_bpm=120,
            base_velocity=1.6,
            tick_rate=1,
        )


class TestDifficalcyManiaDifficultyCalculator:
    def test_enigne(self):
        assert DifficalcyManiaDifficultyCalculator.engine() == "osu.Game.Rulesets.Mania"

    def test_version(self):
        assert DifficalcyManiaDifficultyCalculator.version() == "2025.403.0.0"

    def test_calculate_scores(self):
        calc = DifficalcyManiaDifficultyCalculator()
        score = Score(
            "4",
            mods={NewMods.DOUBLETIME: {}, NewMods.EASY: {}, NewMods.CLASSIC: {}},
            statistics={
                "great": 1,
                "good": 2,
                "ok": 3,
                "meh": 4,
                "miss": 5,
            },
        )
        assert calc.calculate_scores([score]) == [
            Calculation(
                difficulty_values={
                    "total": 2.797245912537965,
                },
                performance_values={
                    "difficulty": 43.17076331130473,
                    "total": 21.585381655652366,
                },
            )
        ]

    def test_get_beatmap_details(self):
        calc = DifficalcyManiaDifficultyCalculator()
        assert calc.get_beatmap_details("4") == BeatmapDetails(
            hitobject_counts={"notes": 123, "hold_notes": 14},
            difficulty_settings={"key_count": 4, "accuracy": 7, "drain_rate": 5},
            artist="Unknown",
            title="Unknown",
            difficulty_name="Normal",
            author="Unknown Creator",
            max_combo=151,
            length=30500,
            mininum_bpm=120,
            maximum_bpm=120,
            common_bpm=120,
            base_velocity=1.6,
            tick_rate=1,
        )


class TestDifficalcyPerformancePlusDifficultyCalculator:
    def test_enigne(self):
        assert (
            DifficalcyPerformancePlusDifficultyCalculator.engine()
            == "https://github.com/Syriiin/osu/tree/performanceplus"
        )

    def test_version(self):
        assert (
            DifficalcyPerformancePlusDifficultyCalculator.version()
            == "faca4a938ce8b71503a5ac9e9ce52e2ae233a2a2"
        )

    def test_calculate_scores(self):
        calc = DifficalcyPerformancePlusDifficultyCalculator()
        score = Score(
            "307618",
            mods={NewMods.DOUBLETIME: {}, NewMods.HIDDEN: {}, NewMods.CLASSIC: {}},
            statistics={
                "ok": 14,
                "meh": 1,
                "miss": 1,
            },
            combo=2000,
        )
        assert calc.calculate_scores([score]) == [
            Calculation(
                difficulty_values={
                    "aim": 2.8804685309467284,
                    "jumpAim": 2.8763118223866133,
                    "flowAim": 1.6727417520197583,
                    "precision": 1.714528074416766,
                    "speed": 3.179656468968935,
                    "stamina": 2.8045880770770752,
                    "accuracy": 1.0546478295311437,
                    "total": 6.123075221732318,
                },
                performance_values={
                    "aim": 68.38232334186907,
                    "jumpAim": 68.08670955755021,
                    "flowAim": 13.391867347855435,
                    "precision": 14.420763347653594,
                    "speed": 99.53445865488443,
                    "stamina": 68.30305130767819,
                    "accuracy": 87.89378488351228,
                    "total": 259.5756907401086,
                },
            )
        ]

    def test_get_beatmap_details(self):
        calc = DifficalcyPerformancePlusDifficultyCalculator()
        assert calc.get_beatmap_details("307618") == BeatmapDetails(
            hitobject_counts={
                "circles": 1093,
                "sliders": 659,
                "spinners": 1,
                "slider_ticks": 346,
            },
            difficulty_settings={
                "circle_size": 4,
                "approach_rate": 8,
                "accuracy": 6,
                "drain_rate": 5,
            },
            artist="senya",
            title="Songs Compilation",
            difficulty_name="Marathon",
            author="Satellite",
            max_combo=2758,
            length=678047,
            mininum_bpm=121,
            maximum_bpm=168,
            common_bpm=138,
            base_velocity=1.7,
            tick_rate=2,
        )
