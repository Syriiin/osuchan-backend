import pytest

from common.osu.difficultycalculator import (
    Calculation,
    CalculationException,
    CalculatorClosedException,
    DifficalcyOsuDifficultyCalculator,
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
            mods=Mods.DOUBLETIME + Mods.HIDDEN,
            count_100=14,
            count_50=1,
            count_miss=1,
            combo=2000,
        )
        assert calc.calculate_score(score) == Calculation(
            difficulty=5.919765949249268, performance=298.1595153808594
        )

    def test_calculate_score_batch(self):
        calc = OppaiDifficultyCalculator()
        scores = [
            Score(
                "307618",
                mods=Mods.DOUBLETIME + Mods.HIDDEN,
                count_100=14,
                count_50=1,
                count_miss=1,
                combo=2000,
            ),
            Score(
                "307618",
                mods=Mods.DOUBLETIME + Mods.HIDDEN + Mods.HARDROCK,
                count_100=14,
                count_50=1,
                count_miss=1,
                combo=2000,
            ),
            Score(
                "307618",
                mods=Mods.DOUBLETIME + Mods.HIDDEN + Mods.HARDROCK,
            ),
        ]
        assert calc.calculate_score_batch(scores) == [
            Calculation(difficulty=5.919765949249268, performance=298.1595153808594),
            Calculation(difficulty=6.20743465423584, performance=476.4307861328125),
            Calculation(difficulty=6.20743465423584, performance=630.419677734375),
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
        assert RosuppDifficultyCalculator.version() == "1.0.0"

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
            mods=Mods.DOUBLETIME + Mods.HIDDEN,
            count_100=14,
            count_50=1,
            count_miss=1,
            combo=2000,
        )
        assert calc.calculate_score(score) == Calculation(
            difficulty=6.264344677869616, performance=312.43705315450256
        )

    def test_calculate_score_batch(self):
        calc = RosuppDifficultyCalculator()
        scores = [
            Score(
                "307618",
                mods=Mods.DOUBLETIME + Mods.HIDDEN,
                count_100=14,
                count_50=1,
                count_miss=1,
                combo=2000,
            ),
            Score(
                "307618",
                mods=Mods.DOUBLETIME + Mods.HIDDEN + Mods.HARDROCK,
                count_100=14,
                count_50=1,
                count_miss=1,
                combo=2000,
            ),
            Score(
                "307618",
                mods=Mods.DOUBLETIME + Mods.HIDDEN + Mods.HARDROCK,
            ),
        ]
        assert calc.calculate_score_batch(scores) == [
            Calculation(difficulty=6.264344677869616, performance=312.43705315450256),
            Calculation(difficulty=6.531051472171891, performance=487.5904861756349),
            Calculation(difficulty=6.531051472171891, performance=655.9388807525456),
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
    def test_enigne(self):
        assert DifficalcyOsuDifficultyCalculator.engine() == "osu.Game.Rulesets.Osu"

    def test_version(self):
        assert DifficalcyOsuDifficultyCalculator.version() == "2024.412.1.0"

    def test_context_manager(self):
        with DifficalcyOsuDifficultyCalculator() as calc:
            assert calc.calculate_score(Score("307618")) == Calculation(
                difficulty=4.4569433791337945, performance=135.0040504515237
            )

    def test_invalid_beatmap(self):
        with pytest.raises(CalculationException):
            with DifficalcyOsuDifficultyCalculator() as calc:
                calc.calculate_score(Score("notarealbeatmap"))

    def test_calculate_score(self):
        calc = DifficalcyOsuDifficultyCalculator()
        score = Score(
            "307618",
            mods=Mods.DOUBLETIME + Mods.HIDDEN,
            count_100=14,
            count_50=1,
            count_miss=1,
            combo=2000,
        )
        assert calc.calculate_score(score) == Calculation(
            difficulty=6.263707394408435, performance=312.36671287580185
        )

    def test_calculate_score_batch(self):
        calc = DifficalcyOsuDifficultyCalculator()
        scores = [
            Score(
                "307618",
                mods=Mods.DOUBLETIME + Mods.HIDDEN,
                count_100=14,
                count_50=1,
                count_miss=1,
                combo=2000,
            ),
            Score(
                "307618",
                mods=Mods.DOUBLETIME + Mods.HIDDEN + Mods.HARDROCK,
                count_100=14,
                count_50=1,
                count_miss=1,
                combo=2000,
            ),
            Score(
                "307618",
                mods=Mods.DOUBLETIME + Mods.HIDDEN + Mods.HARDROCK,
            ),
        ]
        assert calc.calculate_score_batch(scores) == [
            Calculation(difficulty=6.263707394408435, performance=312.36671287580185),
            Calculation(difficulty=6.530286188377548, performance=487.4810004992573),
            Calculation(difficulty=6.530286188377548, performance=655.7872855036575),
        ]
