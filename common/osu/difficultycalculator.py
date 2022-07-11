from abc import ABC, abstractmethod
from contextlib import AbstractContextManager
from importlib import metadata

import oppaipy
import rosu_pp_py

from common.osu.enums import Mods

OPPAIPY_VERSION = metadata.version("oppaipy")
ROSUPP_VERSION = metadata.version("rosu_pp_py")


class DifficultyCalculatorException(Exception):
    pass


class InvalidBeatmapException(DifficultyCalculatorException):
    pass


class CalculationException(DifficultyCalculatorException):
    pass


class DifficultyCalculator(AbstractContextManager, ABC):
    def __init__(self, beatmap_path: str):
        self.beatmap_path = beatmap_path

    def __enter__(self):
        return self

    @abstractmethod
    def __exit__(self, exc_type, exc_value, traceback):
        pass

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def set_accuracy(self, count_100: int, count_50: int) -> None:
        pass

    @abstractmethod
    def set_misses(self, count_miss: int) -> None:
        pass

    @abstractmethod
    def set_combo(self, combo: int) -> None:
        pass

    @abstractmethod
    def set_mods(self, mods: Mods) -> None:
        pass

    @abstractmethod
    def _calculate() -> None:
        pass

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
        pass

    @property
    @abstractmethod
    def performance_total(self) -> float:
        pass

    @property
    @abstractmethod
    def engine(self) -> str:
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        pass


class OppaiDifficultyCalculator(DifficultyCalculator):
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

    @property
    def engine(self):
        return "oppaipy"

    @property
    def version(self):
        return OPPAIPY_VERSION


class RosuppDifficultyCalculator(DifficultyCalculator):
    def __init__(self, beatmap_path: str):
        super().__init__(beatmap_path)
        try:
            self.rosupp_calc = rosu_pp_py.Calculator(beatmap_path)
        except Exception as e:
            raise InvalidBeatmapException(
                f'An error occured in parsing the beatmap "{self.beatmap_path}"'
            ) from e

        self.score_params = rosu_pp_py.ScoreParams()
        self.calc_result = None

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        pass

    def set_accuracy(self, count_100: int, count_50: int):
        self.score_params.n100 = count_100
        self.score_params.n50 = count_50

    def set_misses(self, count_miss: int):
        self.score_params.nMisses = count_miss

    def set_combo(self, combo: int):
        self.score_params.combo = combo

    def set_mods(self, mods: Mods):
        self.score_params.mods = mods

    def _calculate(self):
        [self.calc_result] = self.rosupp_calc.calculate(self.score_params)

    @property
    def difficulty_total(self) -> float:
        return self.calc_result.stars if self.calc_result is not None else 0.0

    @property
    def performance_total(self) -> float:
        return self.calc_result.pp if self.calc_result is not None else 0.0

    @property
    def engine(self):
        return "rosu-pp-py"

    @property
    def version(self):
        return ROSUPP_VERSION
