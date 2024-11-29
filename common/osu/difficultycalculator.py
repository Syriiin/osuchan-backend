from abc import ABC, abstractmethod
from contextlib import AbstractContextManager
from typing import Iterable, NamedTuple, Type

import httpx
from django.conf import settings
from django.utils.module_loading import import_string

from common.osu.enums import Gamemode
from common.osu.utils import get_json_mods

# TODO: lazy load this instead of doing at import
difficalcy_osu_info = httpx.get(f"{settings.DIFFICALCY_OSU_URL}/api/info").json()
difficalcy_taiko_info = httpx.get(f"{settings.DIFFICALCY_TAIKO_URL}/api/info").json()
difficalcy_catch_info = httpx.get(f"{settings.DIFFICALCY_CATCH_URL}/api/info").json()
difficalcy_mania_info = httpx.get(f"{settings.DIFFICALCY_MANIA_URL}/api/info").json()
difficalcy_performanceplus_info = httpx.get(
    f"{settings.DIFFICALCY_PERFORMANCEPLUS_URL}/api/info"
).json()

DIFFICALCY_OSU_ENGINE = difficalcy_osu_info["calculatorPackage"]
DIFFICALCY_OSU_VERSION = difficalcy_osu_info["calculatorVersion"]
DIFFICALCY_TAIKO_ENGINE = difficalcy_taiko_info["calculatorPackage"]
DIFFICALCY_TAIKO_VERSION = difficalcy_taiko_info["calculatorVersion"]
DIFFICALCY_CATCH_ENGINE = difficalcy_catch_info["calculatorPackage"]
DIFFICALCY_CATCH_VERSION = difficalcy_catch_info["calculatorVersion"]
DIFFICALCY_MANIA_ENGINE = difficalcy_mania_info["calculatorPackage"]
DIFFICALCY_MANIA_VERSION = difficalcy_mania_info["calculatorVersion"]
DIFFICALCY_PERFORMANCEPLUS_ENGINE = difficalcy_performanceplus_info["calculatorPackage"]
DIFFICALCY_PERFORMANCEPLUS_VERSION = difficalcy_performanceplus_info[
    "calculatorVersion"
]


class Score(NamedTuple):
    beatmap_id: str
    mods: int | None = None
    is_classic: bool = True
    statistics: dict[str, int] = {}
    combo: int | None = None


class Calculation(NamedTuple):
    difficulty_values: dict[str, float]
    performance_values: dict[str, float]


class DifficultyCalculatorException(Exception):
    pass


class CalculationException(DifficultyCalculatorException):
    pass


class AbstractDifficultyCalculator(AbstractContextManager, ABC):
    def __init__(self):
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._close()

    @abstractmethod
    def _close(self):
        raise NotImplementedError()

    def close(self):
        self.closed = True
        self._close()

    @abstractmethod
    def calculate_scores(self, scores: Iterable[Score]) -> list[Calculation]:
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def engine() -> str:
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def version() -> str:
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def gamemode() -> Gamemode:
        raise NotImplementedError()


class AbstractDifficalcyDifficultyCalculator(AbstractDifficultyCalculator):
    def __init__(self):
        super().__init__()

        self.client = httpx.Client(timeout=180.0)

    def _close(self):
        self.client.close()

    @abstractmethod
    def _get_url(self) -> str:
        raise NotImplementedError()

    @abstractmethod
    def _difficalcy_score_from_score(self, score: Score) -> dict:
        raise NotImplementedError()

    def calculate_scores(self, scores: Iterable[Score]) -> list[Calculation]:
        try:
            response = self.client.post(
                f"{self._get_url()}/api/batch/calculation",
                json=[self._difficalcy_score_from_score(score) for score in scores],
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as e:
            raise CalculationException(
                f"An error occured in calculating the beatmaps {set(score.beatmap_id for score in scores)}: [{e.response.status_code}] {e.response.text}"
            ) from e
        except httpx.HTTPError as e:
            raise CalculationException(
                f"An error occured in calculating the beatmaps {set(score.beatmap_id for score in scores)}: {e}"
            ) from e

        return [
            Calculation(
                difficulty_values=calculation_data["difficulty"],
                performance_values=calculation_data["performance"],
            )
            for calculation_data in data
        ]


class DifficalcyOsuDifficultyCalculator(AbstractDifficalcyDifficultyCalculator):
    def _get_url(self) -> str:
        return settings.DIFFICALCY_OSU_URL

    def _difficalcy_score_from_score(self, score: Score) -> dict:
        return {
            k: v
            for k, v in {
                "BeatmapId": score.beatmap_id,
                "Mods": get_json_mods(
                    score.mods if score.mods is not None else 0, score.is_classic
                ),
                "Combo": score.combo,
                "Misses": score.statistics.get("miss", 0),
                "Mehs": score.statistics.get("meh", 0),
                "Oks": score.statistics.get("ok", 0),
            }.items()
            if v is not None
        }

    @staticmethod
    def engine() -> str:
        return DIFFICALCY_OSU_ENGINE

    @staticmethod
    def version() -> str:
        return DIFFICALCY_OSU_VERSION

    @staticmethod
    def gamemode():
        return Gamemode.STANDARD


class DifficalcyTaikoDifficultyCalculator(AbstractDifficalcyDifficultyCalculator):
    def _get_url(self) -> str:
        return settings.DIFFICALCY_TAIKO_URL

    def _difficalcy_score_from_score(self, score: Score) -> dict:
        return {
            k: v
            for k, v in {
                "BeatmapId": score.beatmap_id,
                "Mods": get_json_mods(
                    score.mods if score.mods is not None else 0, score.is_classic
                ),
                "Combo": score.combo,
                "Misses": score.statistics.get("miss", 0),
                "Oks": score.statistics.get("ok", 0),
            }.items()
            if v is not None
        }

    @staticmethod
    def engine() -> str:
        return DIFFICALCY_TAIKO_ENGINE

    @staticmethod
    def version() -> str:
        return DIFFICALCY_TAIKO_VERSION

    @staticmethod
    def gamemode():
        return Gamemode.TAIKO


class DifficalcyCatchDifficultyCalculator(AbstractDifficalcyDifficultyCalculator):
    def _get_url(self) -> str:
        return settings.DIFFICALCY_CATCH_URL

    def _difficalcy_score_from_score(self, score: Score) -> dict:
        return {
            k: v
            for k, v in {
                "BeatmapId": score.beatmap_id,
                "Mods": get_json_mods(
                    score.mods if score.mods is not None else 0, score.is_classic
                ),
                "Combo": score.combo,
                "Misses": score.statistics.get("miss", 0),
                "SmallDroplets": score.statistics.get("small_tick_hit", 0),
                "LargeDroplets": score.statistics.get("large_tick_hit", 0),
            }.items()
            if v is not None
        }

    @staticmethod
    def engine() -> str:
        return DIFFICALCY_CATCH_ENGINE

    @staticmethod
    def version() -> str:
        return DIFFICALCY_CATCH_VERSION

    @staticmethod
    def gamemode():
        return Gamemode.CATCH


class DifficalcyManiaDifficultyCalculator(AbstractDifficalcyDifficultyCalculator):
    def _get_url(self) -> str:
        return settings.DIFFICALCY_MANIA_URL

    def _difficalcy_score_from_score(self, score: Score) -> dict:
        return {
            k: v
            for k, v in {
                "BeatmapId": score.beatmap_id,
                "Mods": get_json_mods(
                    score.mods if score.mods is not None else 0, score.is_classic
                ),
                "Combo": score.combo,
                "Misses": score.statistics.get("miss", 0),
                "Mehs": score.statistics.get("meh", 0),
                "Oks": score.statistics.get("ok", 0),
                "Goods": score.statistics.get("good", 0),
                "Greats": score.statistics.get("great", 0),
            }.items()
            if v is not None
        }

    @staticmethod
    def engine() -> str:
        return DIFFICALCY_MANIA_ENGINE

    @staticmethod
    def version() -> str:
        return DIFFICALCY_MANIA_VERSION

    @staticmethod
    def gamemode():
        return Gamemode.MANIA


class DifficalcyPerformancePlusDifficultyCalculator(
    AbstractDifficalcyDifficultyCalculator
):
    def _get_url(self) -> str:
        return settings.DIFFICALCY_PERFORMANCEPLUS_URL

    def _difficalcy_score_from_score(self, score: Score) -> dict:
        return {
            k: v
            for k, v in {
                "BeatmapId": score.beatmap_id,
                "Mods": get_json_mods(
                    score.mods if score.mods is not None else 0, score.is_classic
                ),
                "Combo": score.combo,
                "Misses": score.statistics.get("miss", 0),
                "Mehs": score.statistics.get("meh", 0),
                "Oks": score.statistics.get("ok", 0),
            }.items()
            if v is not None
        }

    @staticmethod
    def engine() -> str:
        return DIFFICALCY_PERFORMANCEPLUS_ENGINE

    @staticmethod
    def version() -> str:
        return DIFFICALCY_PERFORMANCEPLUS_VERSION

    @staticmethod
    def gamemode():
        return Gamemode.STANDARD


difficulty_calculators_classes: dict[str, type[AbstractDifficultyCalculator]] = {
    name: import_string(calculator_class)
    for name, calculator_class in settings.DIFFICULTY_CALCULATOR_CLASSES.items()
}


def get_difficulty_calculator_class(name: str) -> Type[AbstractDifficultyCalculator]:
    return difficulty_calculators_classes[name]


def get_difficulty_calculator_class_for_engine(
    engine: str,
) -> Type[AbstractDifficultyCalculator]:
    try:
        return next(
            calculator_class
            for calculator_class in difficulty_calculators_classes.values()
            if calculator_class.engine() == engine
        )
    except StopIteration as e:
        raise ValueError(f"No difficulty calculator found for engine {engine}") from e


def get_default_difficulty_calculator_class(
    gamemode: Gamemode,
) -> Type[AbstractDifficultyCalculator]:
    return get_difficulty_calculator_class(
        settings.DEFAULT_DIFFICULTY_CALCULATORS[gamemode]
    )


def get_difficulty_calculators_for_gamemode(
    gamemode: Gamemode,
) -> list[Type[AbstractDifficultyCalculator]]:
    return [
        calculator_class
        for calculator_class in difficulty_calculators_classes.values()
        if calculator_class.gamemode() == gamemode
    ]
