from abc import ABC, abstractmethod
from contextlib import AbstractContextManager
from typing import Iterable, NamedTuple, Type

import httpx
from django.conf import settings
from django.utils.module_loading import import_string

from common.osu.enums import Gamemode

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
    count_katu: int | None = None  # mania: goods
    count_300: int | None = None  # mania: greats (ignored for others)
    count_100: int | None = None  # oks, catch: large droplets
    count_50: int | None = None  # mehs, catch: small droplets
    count_miss: int | None = None
    combo: int | None = None


class Calculation(NamedTuple):
    difficulty_values: dict[str, float]
    performance_values: dict[str, float]


class DifficultyCalculatorException(Exception):
    pass


class CalculatorClosedException(DifficultyCalculatorException):
    pass


class InvalidBeatmapException(DifficultyCalculatorException):
    pass


class CalculationException(DifficultyCalculatorException):
    pass


class NotYetCalculatedException(DifficultyCalculatorException):
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

    def calculate_score(self, score: Score) -> Calculation:
        self._reset()
        self.set_beatmap(score.beatmap_id)

        if score.mods is not None:
            self.set_mods(score.mods)
        if score.count_100 is not None or score.count_50 is not None:
            self.set_accuracy(score.count_100 or 0, score.count_50 or 0)
        if score.count_miss is not None:
            self.set_misses(score.count_miss)
        if score.combo is not None:
            self.set_combo(score.combo)

        self.calculate()
        return Calculation(
            difficulty_values={"total": self.difficulty_total},
            performance_values={"total": self.performance_total},
        )

    def calculate_score_batch(self, scores: Iterable[Score]) -> list[Calculation]:
        return [self.calculate_score(score) for score in scores]

    @abstractmethod
    def _reset(self):
        raise NotImplementedError()

    @abstractmethod
    def set_beatmap(self, beatmap_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def set_accuracy(self, count_100: int, count_50: int) -> None:
        raise NotImplementedError()

    @abstractmethod
    def set_misses(self, count_miss: int) -> None:
        raise NotImplementedError()

    @abstractmethod
    def set_combo(self, combo: int) -> None:
        raise NotImplementedError()

    @abstractmethod
    def set_mods(self, mods: int) -> None:
        raise NotImplementedError()

    @abstractmethod
    def _calculate(self) -> None:
        raise NotImplementedError()

    def calculate(self) -> None:
        if self.closed:
            raise CalculatorClosedException(
                "calculate() cannot be called on a closed calculator"
            )

        self._calculate()

    @property
    @abstractmethod
    def difficulty_total(self) -> float:
        raise NotImplementedError()

    @property
    @abstractmethod
    def performance_total(self) -> float:
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

    def calculate_score(self, score: Score) -> Calculation:
        try:
            response = self.client.get(
                f"{self._get_url()}/api/calculation",
                params=self._difficalcy_score_from_score(score),
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as e:
            raise CalculationException(
                f"An error occured in calculating the beatmap {score.beatmap_id}: {e.request.url} [{e.response.status_code}] {e.response.text}"
            ) from e
        except httpx.HTTPError as e:
            raise CalculationException(
                f"An error occured in calculating the beatmap {score.beatmap_id}: {e.request.url} - {e}"
            ) from e

        return Calculation(
            difficulty_values=data["difficulty"],
            performance_values=data["performance"],
        )

    def calculate_score_batch(self, scores: Iterable[Score]) -> list[Calculation]:
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

    def _reset(self):
        pass

    def set_beatmap(self, beatmap_id: str) -> None:
        raise NotImplementedError()

    def set_accuracy(self, count_100: int, count_50: int) -> None:
        raise NotImplementedError()

    def set_misses(self, count_miss: int) -> None:
        raise NotImplementedError()

    def set_combo(self, combo: int) -> None:
        raise NotImplementedError()

    def set_mods(self, mods: int) -> None:
        raise NotImplementedError()

    def _calculate(self) -> None:
        raise NotImplementedError()

    @property
    def difficulty_total(self) -> float:
        raise NotImplementedError()

    @property
    def performance_total(self) -> float:
        raise NotImplementedError()


class DifficalcyOsuDifficultyCalculator(AbstractDifficalcyDifficultyCalculator):
    def _get_url(self) -> str:
        return settings.DIFFICALCY_OSU_URL

    def _difficalcy_score_from_score(self, score: Score) -> dict:
        return {
            k: v
            for k, v in {
                "BeatmapId": score.beatmap_id,
                "Mods": score.mods,
                "Combo": score.combo,
                "Misses": score.count_miss,
                "Mehs": score.count_50,
                "Oks": score.count_100,
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
                "Mods": score.mods,
                "Combo": score.combo,
                "Misses": score.count_miss,
                "Oks": score.count_100,
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
                "Mods": score.mods,
                "Combo": score.combo,
                "Misses": score.count_miss,
                "SmallDroplets": score.count_50,
                "LargeDroplets": score.count_100,
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
                "Mods": score.mods,
                "Combo": score.combo,
                "Misses": score.count_miss,
                "Mehs": score.count_50,
                "Oks": score.count_100,
                "Goods": score.count_katu,
                "Greats": score.count_300,
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
                "Mods": score.mods,
                "Combo": score.combo,
                "Misses": score.count_miss,
                "Mehs": score.count_50,
                "Oks": score.count_100,
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
