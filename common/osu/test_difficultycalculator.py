import pytest

from common.osu.difficultycalculator import (
    Calculation,
    CalculationException,
    DifficalcyCatchDifficultyCalculator,
    DifficalcyManiaDifficultyCalculator,
    DifficalcyOsuDifficultyCalculator,
    DifficalcyPerformancePlusDifficultyCalculator,
    DifficalcyTaikoDifficultyCalculator,
    Score,
)
from common.osu.enums import Mods


class TestDifficalcyDifficultyCalculator:
    def test_context_manager(self):
        with DifficalcyOsuDifficultyCalculator() as calc:
            assert calc.calculate_scores([Score("307618")]) == [
                Calculation(
                    difficulty_values={
                        "aim": 2.095341891859337,
                        "speed": 2.1495826614072095,
                        "flashlight": 0,
                        "total": 4.448219767994142,
                    },
                    performance_values={
                        "aim": 44.714749718084626,
                        "speed": 48.549792148960236,
                        "accuracy": 36.07670429437059,
                        "flashlight": 0,
                        "total": 134.70509049106212,
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
                mods=int(Mods.DOUBLETIME + Mods.HIDDEN),
                statistics={
                    "ok": 14,
                    "meh": 1,
                    "miss": 1,
                },
                combo=2000,
            ),
            Score(
                "307618",
                mods=int(Mods.DOUBLETIME + Mods.HIDDEN + Mods.HARDROCK),
                statistics={
                    "ok": 14,
                    "meh": 1,
                    "miss": 1,
                },
                combo=2000,
            ),
            Score(
                "307618",
                mods=int(Mods.DOUBLETIME + Mods.HIDDEN + Mods.HARDROCK),
            ),
        ]
        assert calc.calculate_scores(scores) == [
            Calculation(
                difficulty_values={
                    "aim": 2.9046060098541724,
                    "speed": 3.0467078113308332,
                    "flashlight": 0,
                    "total": 6.239289759183808,
                },
                performance_values={
                    "aim": 119.59317403057803,
                    "speed": 134.24920069361875,
                    "accuracy": 84.96884392557897,
                    "flashlight": 0,
                    "total": 353.20816658310764,
                },
            ),
            Calculation(
                difficulty_values={
                    "aim": 3.151744227705843,
                    "speed": 3.059545698906488,
                    "flashlight": 0,
                    "total": 6.509181160929765,
                },
                performance_values={
                    "aim": 185.9035493619653,
                    "speed": 172.35293950129184,
                    "accuracy": 166.32370945374015,
                    "flashlight": 0,
                    "total": 545.9871409279718,
                },
            ),
            Calculation(
                difficulty_values={
                    "aim": 3.151744227705843,
                    "speed": 3.059545698906488,
                    "flashlight": 0,
                    "total": 6.509181160929765,
                },
                performance_values={
                    "aim": 210.34114835701476,
                    "speed": 204.19435600873052,
                    "accuracy": 212.8087296294707,
                    "flashlight": 0,
                    "total": 652.8833944223771,
                },
            ),
        ]


class TestDifficalcyOsuDifficultyCalculator:
    def test_enigne(self):
        assert DifficalcyOsuDifficultyCalculator.engine() == "osu.Game.Rulesets.Osu"

    def test_version(self):
        assert DifficalcyOsuDifficultyCalculator.version() == "2024.1104.0.0"

    def test_calculate_scores(self):
        calc = DifficalcyOsuDifficultyCalculator()
        score = Score(
            "307618",
            mods=int(Mods.DOUBLETIME + Mods.HIDDEN),
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
                    "aim": 2.9046060098541724,
                    "speed": 3.0467078113308332,
                    "flashlight": 0,
                    "total": 6.239289759183808,
                },
                performance_values={
                    "aim": 119.59317403057803,
                    "speed": 134.24920069361875,
                    "accuracy": 84.96884392557897,
                    "flashlight": 0,
                    "total": 353.20816658310764,
                },
            )
        ]


class TestDifficalcyTaikoDifficultyCalculator:
    def test_enigne(self):
        assert DifficalcyTaikoDifficultyCalculator.engine() == "osu.Game.Rulesets.Taiko"

    def test_version(self):
        assert DifficalcyTaikoDifficultyCalculator.version() == "2024.1104.0.0"

    def test_calculate_scores(self):
        calc = DifficalcyTaikoDifficultyCalculator()
        score = Score(
            "2",
            mods=int(Mods.DOUBLETIME + Mods.HARDROCK),
            statistics={
                "ok": 3,
                "miss": 5,
            },
            combo=150,
        )
        assert calc.calculate_scores([score]) == [
            Calculation(
                difficulty_values={
                    "stamina": 2.30946001517734,
                    "rhythm": 0.06858773903139824,
                    "colour": 1.0836833699674413,
                    "total": 4.0789820318081444,
                },
                performance_values={
                    "difficulty": 73.59571092766963,
                    "accuracy": 151.44363419166947,
                    "total": 240.21864447545653,
                },
            )
        ]


class TestDifficalcyCatchDifficultyCalculator:
    def test_enigne(self):
        assert DifficalcyCatchDifficultyCalculator.engine() == "osu.Game.Rulesets.Catch"

    def test_version(self):
        assert DifficalcyCatchDifficultyCalculator.version() == "2024.1104.0.0"

    def test_calculate_scores(self):
        calc = DifficalcyCatchDifficultyCalculator()
        score = Score(
            "3",
            mods=int(Mods.DOUBLETIME + Mods.HARDROCK),
            statistics={
                "large_tick_hit": 18,
                "small_tick_hit": 200,
                "miss": 5,
            },
            combo=100,
        )
        assert calc.calculate_scores([score]) == [
            Calculation(
                difficulty_values={
                    "total": 5.739025024925008,
                },
                performance_values={
                    "total": 241.19384779497875,
                },
            )
        ]


class TestDifficalcyManiaDifficultyCalculator:
    def test_enigne(self):
        assert DifficalcyManiaDifficultyCalculator.engine() == "osu.Game.Rulesets.Mania"

    def test_version(self):
        assert DifficalcyManiaDifficultyCalculator.version() == "2024.1104.0.0"

    def test_calculate_scores(self):
        calc = DifficalcyManiaDifficultyCalculator()
        score = Score(
            "4",
            mods=int(Mods.DOUBLETIME + Mods.EASY),
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
            mods=int(Mods.DOUBLETIME + Mods.HIDDEN),
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
