import pytest

from common.osu.difficultycalculator import (
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
    def test_context_manager(self, snapshot):
        with DifficalcyOsuDifficultyCalculator() as calc:
            assert (
                calc.calculate_scores([Score("307618", mods={Mods.CLASSIC: {}})])
                == snapshot
            )

    def test_invalid_beatmap(self):
        with pytest.raises(CalculationException):
            with DifficalcyOsuDifficultyCalculator() as calc:
                calc.calculate_scores([Score("notarealbeatmap")])

    def test_calculate_scores(self, snapshot):
        calc = DifficalcyOsuDifficultyCalculator()
        scores = [
            Score(
                "307618",
                mods={Mods.DOUBLETIME: {}, Mods.HIDDEN: {}, Mods.CLASSIC: {}},
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
                    Mods.DOUBLETIME: {},
                    Mods.HIDDEN: {},
                    Mods.HARDROCK: {},
                    Mods.CLASSIC: {},
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
                    Mods.DOUBLETIME: {},
                    Mods.HIDDEN: {},
                    Mods.HARDROCK: {},
                    Mods.CLASSIC: {},
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
        assert calc.calculate_scores(scores) == snapshot


class TestDifficalcyOsuDifficultyCalculator:
    def test_enigne(self):
        assert DifficalcyOsuDifficultyCalculator.engine() == "osu.Game.Rulesets.Osu"

    def test_version(self):
        assert DifficalcyOsuDifficultyCalculator.version() == "2025.710.0.0"

    def test_calculate_scores(self, snapshot):
        calc = DifficalcyOsuDifficultyCalculator()
        score = Score(
            "307618",
            mods={Mods.DOUBLETIME: {}, Mods.HIDDEN: {}, Mods.CLASSIC: {}},
            statistics={
                "ok": 14,
                "meh": 1,
                "miss": 1,
            },
            combo=2000,
        )
        assert calc.calculate_scores([score]) == snapshot

    def test_get_beatmap_details(self, snapshot):
        calc = DifficalcyOsuDifficultyCalculator()
        assert calc.get_beatmap_details("307618") == snapshot


class TestDifficalcyTaikoDifficultyCalculator:
    def test_enigne(self):
        assert DifficalcyTaikoDifficultyCalculator.engine() == "osu.Game.Rulesets.Taiko"

    def test_version(self):
        assert DifficalcyTaikoDifficultyCalculator.version() == "2025.710.0.0"

    def test_calculate_scores(self, snapshot):
        calc = DifficalcyTaikoDifficultyCalculator()
        score = Score(
            "2",
            mods={Mods.DOUBLETIME: {}, Mods.HARDROCK: {}, Mods.CLASSIC: {}},
            statistics={
                "ok": 3,
                "miss": 5,
            },
            combo=150,
        )
        assert calc.calculate_scores([score]) == snapshot

    def test_get_beatmap_details(self, snapshot):
        calc = DifficalcyTaikoDifficultyCalculator()
        assert calc.get_beatmap_details("2") == snapshot


class TestDifficalcyCatchDifficultyCalculator:
    def test_enigne(self):
        assert DifficalcyCatchDifficultyCalculator.engine() == "osu.Game.Rulesets.Catch"

    def test_version(self):
        assert DifficalcyCatchDifficultyCalculator.version() == "2025.710.0.0"

    def test_calculate_scores(self, snapshot):
        calc = DifficalcyCatchDifficultyCalculator()
        score = Score(
            "3",
            mods={Mods.DOUBLETIME: {}, Mods.HARDROCK: {}, Mods.CLASSIC: {}},
            statistics={
                "large_tick_hit": 18,
                "small_tick_hit": 200,
                "miss": 5,
            },
            combo=100,
        )
        assert calc.calculate_scores([score]) == snapshot

    def test_get_beatmap_details(self, snapshot):
        calc = DifficalcyCatchDifficultyCalculator()
        assert calc.get_beatmap_details("3") == snapshot


class TestDifficalcyManiaDifficultyCalculator:
    def test_enigne(self):
        assert DifficalcyManiaDifficultyCalculator.engine() == "osu.Game.Rulesets.Mania"

    def test_version(self):
        assert DifficalcyManiaDifficultyCalculator.version() == "2025.710.0.0"

    def test_calculate_scores(self, snapshot):
        calc = DifficalcyManiaDifficultyCalculator()
        score = Score(
            "4",
            mods={Mods.DOUBLETIME: {}, Mods.EASY: {}, Mods.CLASSIC: {}},
            statistics={
                "great": 1,
                "good": 2,
                "ok": 3,
                "meh": 4,
                "miss": 5,
            },
        )
        assert calc.calculate_scores([score]) == snapshot

    def test_get_beatmap_details(self, snapshot):
        calc = DifficalcyManiaDifficultyCalculator()
        assert calc.get_beatmap_details("4") == snapshot


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

    def test_calculate_scores(self, snapshot):
        calc = DifficalcyPerformancePlusDifficultyCalculator()
        score = Score(
            "307618",
            mods={Mods.DOUBLETIME: {}, Mods.HIDDEN: {}, Mods.CLASSIC: {}},
            statistics={
                "ok": 14,
                "meh": 1,
                "miss": 1,
            },
            combo=2000,
        )
        assert calc.calculate_scores([score]) == snapshot

    def test_get_beatmap_details(self, snapshot):
        calc = DifficalcyPerformancePlusDifficultyCalculator()
        assert calc.get_beatmap_details("307618") == snapshot
