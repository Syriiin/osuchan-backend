from abc import ABC, abstractmethod
from contextlib import AbstractContextManager
from importlib import metadata
from typing import Type

import oppaipy
import rosu_pp_py
from django.conf import settings
from django.utils.module_loading import import_string

from common.osu.enums import Mods

OPPAIPY_VERSION = metadata.version("oppaipy")
ROSUPP_VERSION = metadata.version("rosu_pp_py")


class DifficultyCalculatorException(Exception):
    pass


class InvalidBeatmapException(DifficultyCalculatorException):
    pass


class CalculationException(DifficultyCalculatorException):
    pass


class AbstractDifficultyCalculator(AbstractContextManager, ABC):
    def __init__(self, beatmap_path: str):
        self.beatmap_path = beatmap_path

    def __enter__(self):
        return self

    @abstractmethod
    def __exit__(self, exc_type, exc_value, traceback):
        raise NotImplementedError()

    @abstractmethod
    def close(self):
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
    def set_mods(self, mods: Mods) -> None:
        raise NotImplementedError()

    @abstractmethod
    def _calculate() -> None:
        raise NotImplementedError()

    def calculate(self) -> None:
        try:
            self._calculate()
        except Exception as e:
            raise CalculationException(
                f'An error occured in calculating the beatmap "{self.beatmap_path}"'
            ) from e

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
    def __init__(self, beatmap_path: str):
        super().__init__(beatmap_path)
        self.oppai_calc = oppaipy.Calculator(beatmap_path)

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        self.oppai_calc.close()

    def set_accuracy(self, count_100: int, count_50: int):
        self.oppai_calc.set_accuracy(count_100, count_50)

    def set_misses(self, count_miss: int):
        self.oppai_calc.set_misses(count_miss)

    def set_combo(self, combo: int):
        self.oppai_calc.set_combo(combo)

    def set_mods(self, mods: Mods):
        self.oppai_calc.set_mods(mods)

    def _calculate(self):
        self.oppai_calc.calculate()

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
    def __init__(self, beatmap_path: str):
        super().__init__(beatmap_path)
        try:
            self.rosupp_calc = rosu_pp_py.Calculator()
            self.beatmap = rosu_pp_py.Beatmap(path=beatmap_path)
        except Exception as e:
            raise InvalidBeatmapException(
                f'An error occured in parsing the beatmap "{self.beatmap_path}"'
            ) from e

        self.calc_result = None

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        pass

    def set_accuracy(self, count_100: int, count_50: int):
        self.rosupp_calc.set_n100(count_100)
        self.rosupp_calc.set_n50(count_50)

    def set_misses(self, count_miss: int):
        self.rosupp_calc.set_n_misses(count_miss)

    def set_combo(self, combo: int):
        self.rosupp_calc.set_combo(combo)

    def set_mods(self, mods: Mods):
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
