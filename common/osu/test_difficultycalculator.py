import pytest

from common.osu.difficultycalculator import (
    Calculation,
    CalculationException,
    CalculatorClosedException,
    DifficalcyCatchDifficultyCalculator,
    DifficalcyManiaDifficultyCalculator,
    DifficalcyOsuDifficultyCalculator,
    DifficalcyPerformancePlusDifficultyCalculator,
    DifficalcyTaikoDifficultyCalculator,
    InvalidBeatmapException,
    OppaiDifficultyCalculator,
    RosuppDifficultyCalculator,
    Score,
)
from common.osu.enums import Mods


class TestOppaiDifficultyCalculator:
    def test_enigne(self):
        assert OppaiDifficultyCalculator.engine() == "oppaipy"

    def test_version(self):
        assert OppaiDifficultyCalculator.version() == "1.0.4"

    def test_context_manager(self):
        with OppaiDifficultyCalculator() as calc:
            calc.set_beatmap("307618")
            calc.calculate()
            assert calc.difficulty_total == 4.200401306152344

    def test_invalid_beatmap(self):
        with pytest.raises(InvalidBeatmapException):
            with OppaiDifficultyCalculator() as calc:
                calc.set_beatmap("notarealbeatmap")
                calc.calculate()

    def test_calculate_score(self):
        calc = OppaiDifficultyCalculator()
        score = Score(
            "307618",
            mods=int(Mods.DOUBLETIME + Mods.HIDDEN),
            count_100=14,
            count_50=1,
            count_miss=1,
            combo=2000,
        )
        assert calc.calculate_score(score) == Calculation(
            difficulty_values={"total": 5.919765949249268},
            performance_values={"total": 298.1595153808594},
        )

    def test_calculate_score_batch(self):
        calc = OppaiDifficultyCalculator()
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
                difficulty_values={"total": 5.919765949249268},
                performance_values={"total": 298.1595153808594},
            ),
            Calculation(
                difficulty_values={"total": 6.20743465423584},
                performance_values={"total": 476.4307861328125},
            ),
            Calculation(
                difficulty_values={"total": 6.20743465423584},
                performance_values={"total": 630.419677734375},
            ),
        ]

    @pytest.fixture
    def calc(self):
        calc = OppaiDifficultyCalculator()
        calc.set_beatmap("307618")
        calc.calculate()
        return calc

    def test_difficulty_total(self, calc: OppaiDifficultyCalculator):
        assert calc.difficulty_total == 4.200401306152344

    def test_performance_total(self, calc: OppaiDifficultyCalculator):
        assert calc.performance_total == 126.96746063232422

    def test_close(self, calc: OppaiDifficultyCalculator):
        calc.close()
        with pytest.raises(CalculatorClosedException):
            calc.calculate()

    def test_set_accuracy(self, calc: OppaiDifficultyCalculator):
        calc.set_accuracy(14, 1)
        calc.calculate()
        assert calc.difficulty_total == 4.200401306152344
        assert calc.performance_total == 118.77462005615234

    def test_set_misses(self, calc: OppaiDifficultyCalculator):
        calc.set_misses(1)
        calc.calculate()
        assert calc.difficulty_total == 4.200401306152344
        assert calc.performance_total == 123.09051513671875

    def test_set_combo(self, calc: OppaiDifficultyCalculator):
        calc.set_combo(2000)
        calc.calculate()
        assert calc.difficulty_total == 4.200401306152344
        assert calc.performance_total == 106.42977142333984

    def test_set_mods(self, calc: OppaiDifficultyCalculator):
        calc.set_mods(Mods.DOUBLETIME + Mods.HIDDEN)
        calc.calculate()
        assert calc.difficulty_total == 5.919765949249268
        assert calc.performance_total == 397.2521057128906


class TestRosuppDifficultyCalculator:
    def test_enigne(self):
        assert RosuppDifficultyCalculator.engine() == "rosu-pp-py"

    def test_version(self):
        assert RosuppDifficultyCalculator.version() == "1.0.1"

    def test_context_manager(self):
        with RosuppDifficultyCalculator() as calc:
            calc.set_beatmap("307618")
            calc.calculate()
            assert calc.difficulty_total == 4.457399442092882

    def test_invalid_beatmap(self):
        with pytest.raises(InvalidBeatmapException):
            with RosuppDifficultyCalculator() as calc:
                calc.set_beatmap("notarealbeatmap")

    def test_calculate_score(self):
        calc = RosuppDifficultyCalculator()
        score = Score(
            "307618",
            mods=int(Mods.DOUBLETIME + Mods.HIDDEN),
            count_100=14,
            count_50=1,
            count_miss=1,
            combo=2000,
        )
        assert calc.calculate_score(score) == Calculation(
            difficulty_values={"total": 6.264344677869616},
            performance_values={"total": 312.43705315450256},
        )

    def test_calculate_score_batch(self):
        calc = RosuppDifficultyCalculator()
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
                difficulty_values={"total": 6.264344677869616},
                performance_values={"total": 312.43705315450256},
            ),
            Calculation(
                difficulty_values={"total": 6.531051472171891},
                performance_values={"total": 487.5904861756349},
            ),
            Calculation(
                difficulty_values={"total": 6.531051472171891},
                performance_values={"total": 655.9388807525456},
            ),
        ]

    @pytest.fixture
    def calc(self):
        calc = RosuppDifficultyCalculator()
        calc.set_beatmap("307618")
        calc.calculate()
        return calc

    def test_difficulty_total(self, calc: RosuppDifficultyCalculator):
        assert calc.difficulty_total == 4.457399442092882

    def test_performance_total(self, calc: RosuppDifficultyCalculator):
        assert calc.performance_total == 135.0350130086423

    def test_close(self, calc: RosuppDifficultyCalculator):
        calc.close()
        with pytest.raises(CalculatorClosedException):
            calc.calculate()

    def test_set_accuracy(self, calc: RosuppDifficultyCalculator):
        calc.set_accuracy(14, 1)
        calc.calculate()
        assert calc.difficulty_total == 4.457399442092882
        assert calc.performance_total == 124.11285312370458

    def test_set_misses(self, calc: RosuppDifficultyCalculator):
        calc.set_misses(1)
        calc.calculate()
        assert calc.difficulty_total == 4.457399442092882
        assert calc.performance_total == 130.60976567558188

    def test_set_combo(self, calc: RosuppDifficultyCalculator):
        calc.set_combo(2000)
        calc.calculate()
        assert calc.difficulty_total == 4.457399442092882
        assert calc.performance_total == 112.78045221645286

    def test_set_mods(self, calc: RosuppDifficultyCalculator):
        calc.set_mods(Mods.DOUBLETIME + Mods.HIDDEN)
        calc.calculate()
        assert calc.difficulty_total == 6.264344677869616
        assert calc.performance_total == 425.8065805918235


class TestDifficalcyDifficultyCalculator:
    def test_context_manager(self):
        with DifficalcyOsuDifficultyCalculator() as calc:
            assert calc.calculate_score(Score("307618")) == Calculation(
                difficulty_values={
                    "aim": 2.08629357857818,
                    "speed": 2.1778593015565684,
                    "flashlight": 0,
                    "total": 4.4569433791337945,
                },
                performance_values={
                    "aim": 44.12278272319251,
                    "speed": 50.54174287197802,
                    "accuracy": 36.07670429437059,
                    "flashlight": 0,
                    "total": 135.0040504515237,
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
                    "aim": 2.892063051954271,
                    "speed": 3.0958487396004704,
                    "flashlight": 0,
                    "total": 6.263707394408435,
                },
                performance_values={
                    "aim": 98.6032935956297,
                    "speed": 118.92511309917593,
                    "accuracy": 84.96884392557897,
                    "flashlight": 0,
                    "total": 312.36671287580185,
                },
            ),
            Calculation(
                difficulty_values={
                    "aim": 3.1381340530266333,
                    "speed": 3.1129549941521066,
                    "flashlight": 0,
                    "total": 6.530286188377548,
                },
                performance_values={
                    "aim": 153.058022351103,
                    "speed": 153.10941688245896,
                    "accuracy": 166.32370945374015,
                    "flashlight": 0,
                    "total": 487.4810004992573,
                },
            ),
            Calculation(
                difficulty_values={
                    "aim": 3.1381340530266333,
                    "speed": 3.1129549941521066,
                    "flashlight": 0,
                    "total": 6.530286188377548,
                },
                performance_values={
                    "aim": 207.5808620241847,
                    "speed": 215.2746980112218,
                    "accuracy": 212.8087296294707,
                    "flashlight": 0,
                    "total": 655.7872855036575,
                },
            ),
        ]


class TestDifficalcyOsuDifficultyCalculator:
    def test_enigne(self):
        assert DifficalcyOsuDifficultyCalculator.engine() == "osu.Game.Rulesets.Osu"

    def test_version(self):
        assert DifficalcyOsuDifficultyCalculator.version() == "2024.523.0.0"

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
                "aim": 2.892063051954271,
                "speed": 3.0958487396004704,
                "flashlight": 0,
                "total": 6.263707394408435,
            },
            performance_values={
                "aim": 98.6032935956297,
                "speed": 118.92511309917593,
                "accuracy": 84.96884392557897,
                "flashlight": 0,
                "total": 312.36671287580185,
            },
        )


class TestDifficalcyTaikoDifficultyCalculator:
    def test_enigne(self):
        assert DifficalcyTaikoDifficultyCalculator.engine() == "osu.Game.Rulesets.Taiko"

    def test_version(self):
        assert DifficalcyTaikoDifficultyCalculator.version() == "2024.523.0.0"

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
                "difficulty": 65.7817691637774,
                "accuracy": 100.62055832247681,
                "total": 176.94088597258678,
            },
        )


class TestDifficalcyCatchDifficultyCalculator:
    def test_enigne(self):
        assert DifficalcyCatchDifficultyCalculator.engine() == "osu.Game.Rulesets.Catch"

    def test_version(self):
        assert DifficalcyCatchDifficultyCalculator.version() == "2024.523.0.0"

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
                "total": 5.739025024925009,
            },
            performance_values={
                "total": 241.19384779497875,
            },
        )


class TestDifficalcyManiaDifficultyCalculator:
    def test_enigne(self):
        assert DifficalcyManiaDifficultyCalculator.engine() == "osu.Game.Rulesets.Mania"

    def test_version(self):
        assert DifficalcyManiaDifficultyCalculator.version() == "2024.523.0.0"

    def test_calculate_score(self):
        calc = DifficalcyManiaDifficultyCalculator()
        score = Score(
            "4",
            mods=int(Mods.DOUBLETIME),
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
                "difficulty": 5.3963454139130915,
                "total": 43.17076331130473,
            },
        )


class TestDifficalcyPerformancePlusDifficultyCalculator:
    def test_enigne(self):
        assert (
            DifficalcyPerformancePlusDifficultyCalculator.engine()
            == "https://github.com/Syriiin/osu"
        )

    def test_version(self):
        assert (
            DifficalcyPerformancePlusDifficultyCalculator.version()
            == "bec9a43e5984fa755606dc2e60666ef6f3dfeb56"
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
