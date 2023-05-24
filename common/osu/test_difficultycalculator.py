from importlib import metadata
from pathlib import Path

import pytest

from common.osu.difficultycalculator import (
    CalculationException,
    CalculatorClosedException,
    InvalidBeatmapException,
    OppaiDifficultyCalculator,
    RosuppDifficultyCalculator,
)
from common.osu.enums import Mods


class TestOppaiDifficultyCalculator:
    def test_enigne(self):
        assert OppaiDifficultyCalculator.engine() == "oppaipy"

    def test_version(self):
        assert OppaiDifficultyCalculator.version() == metadata.version("oppaipy")

    def test_context_manager(self):
        with OppaiDifficultyCalculator(
            f"{Path(__file__).parent}/testdata/307618.osu"
        ) as calc:
            calc.calculate()
            assert calc.difficulty_total == 4.200401306152344

    def test_invalid_beatmap(self):
        with pytest.raises(CalculationException):
            with OppaiDifficultyCalculator(
                f"{Path(__file__).parent}/testdata/empty.osu"
            ) as calc:
                calc.calculate()

    @pytest.fixture
    def calc(self):
        calc = OppaiDifficultyCalculator(f"{Path(__file__).parent}/testdata/307618.osu")
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
        assert RosuppDifficultyCalculator.version() == metadata.version("rosu-pp-py")

    def test_context_manager(self):
        with RosuppDifficultyCalculator(
            f"{Path(__file__).parent}/testdata/307618.osu"
        ) as calc:
            assert calc.difficulty_total == 4.457399442092882

    def test_invalid_beatmap(self):
        with pytest.raises(InvalidBeatmapException):
            RosuppDifficultyCalculator(f"{Path(__file__).parent}/testdata/empty.osu")

    @pytest.fixture
    def calc(self):
        calc = RosuppDifficultyCalculator(
            f"{Path(__file__).parent}/testdata/307618.osu"
        )
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
        assert calc.performance_total == 124.11285312370455

    def test_set_misses(self, calc: RosuppDifficultyCalculator):
        calc.set_misses(1)
        calc.calculate()
        assert calc.difficulty_total == 4.457399442092882
        assert calc.performance_total == 130.64187056414588

    def test_set_combo(self, calc: RosuppDifficultyCalculator):
        calc.set_combo(2000)
        calc.calculate()
        assert calc.difficulty_total == 4.457399442092882
        assert calc.performance_total == 112.78045221645286

    def test_set_mods(self, calc: RosuppDifficultyCalculator):
        calc.set_mods(Mods.DOUBLETIME + Mods.HIDDEN)
        calc.calculate()
        assert calc.difficulty_total == 6.264344677869616
        assert calc.performance_total == 425.80658059182343
