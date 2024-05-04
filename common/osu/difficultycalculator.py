from abc import ABC, abstractmethod
from contextlib import AbstractContextManager
from importlib import metadata
from typing import Type

import oppaipy
import rosu_pp_py
from django.conf import settings
from django.utils.module_loading import import_string

from common.osu.beatmap_provider import BeatmapNotFoundException, BeatmapProvider

OPPAIPY_VERSION = metadata.version("oppaipy")
ROSUPP_VERSION = metadata.version("rosu_pp_py")


class DifficultyCalculatorException(Exception):
    pass


class CalculatorClosedException(DifficultyCalculatorException):
    pass


class InvalidBeatmapException(DifficultyCalculatorException):
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
    def _calculate() -> None:
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


class OppaiDifficultyCalculator(AbstractDifficultyCalculator):
    def __init__(self):
        super().__init__()

        self.oppai_calc = None
        self.beatmap_path = None

    def _close(self):
        if self.oppai_calc is not None:
            self.oppai_calc.close()

    def set_beatmap(self, beatmap_id: str) -> None:
        beatmap_provider = BeatmapProvider()
        try:
            self.beatmap_path = beatmap_provider.get_beatmap_file(beatmap_id)
        except BeatmapNotFoundException as e:
            raise InvalidBeatmapException(
                f"An error occured in fetching the beatmap {beatmap_id}"
            ) from e
        self.oppai_calc = oppaipy.Calculator(self.beatmap_path)

    def set_accuracy(self, count_100: int, count_50: int):
        self.oppai_calc.set_accuracy(count_100, count_50)

    def set_misses(self, count_miss: int):
        self.oppai_calc.set_misses(count_miss)

    def set_combo(self, combo: int):
        self.oppai_calc.set_combo(combo)

    def set_mods(self, mods: int):
        self.oppai_calc.set_mods(mods)

    def _calculate(self):
        try:
            self.oppai_calc.calculate()
        except oppaipy.OppaiError as e:
            raise CalculationException(
                f'An error occured in calculating the beatmap "{self.beatmap_path}"'
            ) from e

    @property
    def difficulty_total(self):
        return self.oppai_calc.stars

    @property
    def performance_total(self):
        return self.oppai_calc.pp

    @staticmethod
    def engine():
        return "oppaipy"

    @staticmethod
    def version():
        return OPPAIPY_VERSION


class RosuppDifficultyCalculator(AbstractDifficultyCalculator):
    def __init__(self):
        super().__init__()

        self.rosupp_calc = rosu_pp_py.Calculator()

    def _close(self):
        pass

    def set_beatmap(self, beatmap_id: str) -> None:
        beatmap_provider = BeatmapProvider()
        try:
            beatmap_path = beatmap_provider.get_beatmap_file(beatmap_id)
        except BeatmapNotFoundException as e:
            raise InvalidBeatmapException(
                f"An error occured in fetching the beatmap {beatmap_id}"
            ) from e

        try:
            self.beatmap = rosu_pp_py.Beatmap(path=beatmap_path)
        except Exception as e:
            raise InvalidBeatmapException(
                f'An error occured in parsing the beatmap "{self.beatmap_path}"'
            ) from e

    def set_accuracy(self, count_100: int, count_50: int):
        self.rosupp_calc.set_n100(count_100)
        self.rosupp_calc.set_n50(count_50)

    def set_misses(self, count_miss: int):
        self.rosupp_calc.set_n_misses(count_miss)

    def set_combo(self, combo: int):
        self.rosupp_calc.set_combo(combo)

    def set_mods(self, mods: int):
        self.rosupp_calc.set_mods(mods)

    def _calculate(self):
        # rosu_pp_py does lazy calculations it seems
        pass

    @property
    def difficulty_total(self) -> float:
        # TODO: PR to rosu-pp-py to add real type hints here
        return self.rosupp_calc.difficulty(self.beatmap).stars or 0.0  # type: ignore

    @property
    def performance_total(self) -> float:
        return self.rosupp_calc.performance(self.beatmap).pp or 0.0  # type: ignore

    @staticmethod
    def engine():
        return "rosu-pp-py"

    @staticmethod
    def version():
        return ROSUPP_VERSION


DifficultyCalculator: Type[AbstractDifficultyCalculator] = import_string(
    settings.DIFFICULTY_CALCULATOR_CLASS
)
