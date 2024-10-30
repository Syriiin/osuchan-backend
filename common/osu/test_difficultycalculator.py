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
            assert calc.calculate_score(Score("307618")) == Calculation(
                difficulty_values={
                    "aim": 2.095341891859337,
                    "speed": 2.1495826614072095,
                    "flashlight": 0,
                    "total": 4.448219767994142,
                },
                performance_values={
                    "aim": 44.560566997239285,
                    "speed": 48.549792148960236,
                    "accuracy": 40.396026503167406,
                    "flashlight": 0,
                    "total": 138.97827988389787,
                },
            )

    def test_invalid_beatmap(self):
        with pytest.raises(CalculationException):
            with DifficalcyOsuDifficultyCalculator() as calc:
                calc.calculate_score(Score("notarealbeatmap"))

    def test_calculate_score_batch(self):
        calc = DifficalcyOsuDifficultyCalculator()
        scores = [
            Score(
                "307618",
                mods=int(Mods.DOUBLETIME + Mods.HIDDEN),
                count_100=14,
                count_50=1,
                count_miss=1,
                combo=2000,
            ),
            Score(
                "307618",
                mods=int(Mods.DOUBLETIME + Mods.HIDDEN + Mods.HARDROCK),
                count_100=14,
                count_50=1,
                count_miss=1,
                combo=2000,
            ),
            Score(
                "307618",
                mods=int(Mods.DOUBLETIME + Mods.HIDDEN + Mods.HARDROCK),
            ),
        ]
        assert calc.calculate_score_batch(scores) == [
            Calculation(
                difficulty_values={
                    "aim": 2.9046060098541724,
                    "speed": 3.0467078113308332,
                    "flashlight": 0,
                    "total": 6.239289759183808,
                },
                performance_values={
                    "aim": 121.43416388591694,
                    "speed": 136.91391089161527,
                    "accuracy": 104.41454212776276,
                    "flashlight": 0,
                    "total": 377.7534365915769,
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
                    "aim": 187.71259106036473,
                    "speed": 175.7728925639758,
                    "accuracy": 204.38802230631848,
                    "flashlight": 0,
                    "total": 591.0959697257573,
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
                    "aim": 207.50129239752042,
                    "speed": 204.19435600873052,
                    "accuracy": 238.28748358144517,
                    "flashlight": 0,
                    "total": 676.6012597688499,
                },
            ),
        ]


class TestDifficalcyOsuDifficultyCalculator:
    def test_enigne(self):
        assert DifficalcyOsuDifficultyCalculator.engine() == "osu.Game.Rulesets.Osu"

    def test_version(self):
        assert DifficalcyOsuDifficultyCalculator.version() == "2024.1023.0.0"

    def test_calculate_score(self):
        calc = DifficalcyOsuDifficultyCalculator()
        score = Score(
            "307618",
            mods=int(Mods.DOUBLETIME + Mods.HIDDEN),
            count_100=14,
            count_50=1,
            count_miss=1,
            combo=2000,
        )
        assert calc.calculate_score(score) == Calculation(
            difficulty_values={
                "aim": 2.9046060098541724,
                "speed": 3.0467078113308332,
                "flashlight": 0,
                "total": 6.239289759183808,
            },
            performance_values={
                "aim": 121.43416388591694,
                "speed": 136.91391089161527,
                "accuracy": 104.41454212776276,
                "flashlight": 0,
                "total": 377.7534365915769,
            },
        )


class TestDifficalcyTaikoDifficultyCalculator:
    def test_enigne(self):
        assert DifficalcyTaikoDifficultyCalculator.engine() == "osu.Game.Rulesets.Taiko"

    def test_version(self):
        assert DifficalcyTaikoDifficultyCalculator.version() == "2024.1023.0.0"

    def test_calculate_score(self):
        calc = DifficalcyTaikoDifficultyCalculator()
        score = Score(
            "2",
            mods=int(Mods.DOUBLETIME + Mods.HARDROCK),
            count_100=3,
            count_miss=5,
            combo=150,
        )
        assert calc.calculate_score(score) == Calculation(
            difficulty_values={
                "stamina": 2.30946001517734,
                "rhythm": 0.06858773903139824,
                "colour": 1.0836833699674413,
                "total": 4.0789820318081444,
            },
            performance_values={
                "difficulty": 73.62180913301319,
                "accuracy": 151.44363419166947,
                "total": 240.24516772998618,
            },
        )


class TestDifficalcyCatchDifficultyCalculator:
    def test_enigne(self):
        assert DifficalcyCatchDifficultyCalculator.engine() == "osu.Game.Rulesets.Catch"

    def test_version(self):
        assert DifficalcyCatchDifficultyCalculator.version() == "2024.1023.0.0"

    def test_calculate_score(self):
        calc = DifficalcyCatchDifficultyCalculator()
        score = Score(
            "3",
            mods=int(Mods.DOUBLETIME + Mods.HARDROCK),
            count_100=18,
            count_50=200,
            count_miss=5,
            combo=100,
        )
        assert calc.calculate_score(score) == Calculation(
            difficulty_values={
                "total": 5.739025024925008,
            },
            performance_values={
                "total": 241.19384779497875,
            },
        )


class TestDifficalcyManiaDifficultyCalculator:
    def test_enigne(self):
        assert DifficalcyManiaDifficultyCalculator.engine() == "osu.Game.Rulesets.Mania"

    def test_version(self):
        assert DifficalcyManiaDifficultyCalculator.version() == "2024.1023.0.0"

    def test_calculate_score(self):
        calc = DifficalcyManiaDifficultyCalculator()
        score = Score(
            "4",
            mods=int(Mods.DOUBLETIME + Mods.EASY),
            count_300=1,
            count_katu=2,
            count_100=3,
            count_50=4,
            count_miss=5,
        )
        assert calc.calculate_score(score) == Calculation(
            difficulty_values={
                "total": 2.797245912537965,
            },
            performance_values={
                "difficulty": 43.17076331130473,
                "total": 21.585381655652366,
            },
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

    def test_calculate_score(self):
        calc = DifficalcyPerformancePlusDifficultyCalculator()
        score = Score(
            "307618",
            mods=int(Mods.DOUBLETIME + Mods.HIDDEN),
            count_100=14,
            count_50=1,
            count_miss=1,
            combo=2000,
        )
        assert calc.calculate_score(score) == Calculation(
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
