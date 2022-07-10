from abc import ABC, abstractmethod
from contextlib import AbstractContextManager
from importlib import metadata

import oppaipy

from common.osu.enums import Mods

OPPAIPY_VERSION = metadata.version("oppaipy")


class DifficultyCalculator(AbstractContextManager, ABC):
    @abstractmethod
    def __init__(self, beatmap_path: str):
        pass

    def __enter__(self):
        return self

    @abstractmethod
    def __exit__(self, exc_type, exc_value, traceback):
        pass

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def set_accuracy(self, count_100: int, count_50: int):
        pass

    @abstractmethod
    def set_misses(self, count_miss: int):
        pass

    @abstractmethod
    def set_combo(self, combo: int):
        pass

    @abstractmethod
    def set_mods(self, mods: Mods):
        pass

    @abstractmethod
    def calculate(self):
        pass

    @property
    @abstractmethod
    def difficulty_total(self):
        pass

    @property
    @abstractmethod
    def performance_total(self):
        pass

    @property
    @abstractmethod
    def engine(self):
        pass

    @property
    @abstractmethod
    def version(self):
        pass


class OppaiDifficultyCalculator(DifficultyCalculator):
    def __init__(self, beatmap_path: str):
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

    def calculate(self):
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
