import random
from abc import ABC, abstractmethod
from typing import Any

from minigames.games.base import GameScore


class BaseTask(ABC):
    _registry: dict[str, type[BaseTask]] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._registry[cls.type_key] = cls

    type_key: str = ""
    description_template: str = ""

    @classmethod
    @abstractmethod
    def generate_params(cls) -> dict[str, Any]: ...

    @classmethod
    @abstractmethod
    def check(cls, score: GameScore, params: dict[str, Any]) -> bool: ...

    @classmethod
    def get_description(cls, params: dict[str, Any]) -> str:
        return cls.description_template.format(**params)


class AccuracyAboveTask(BaseTask):
    type_key = "accuracy_above"
    description_template = "Get above {value}% accuracy"

    @classmethod
    def generate_params(cls):
        return {"value": random.choice(range(97, 100))}

    @classmethod
    def check(cls, score, params):
        return score.score_accuracy >= params["value"]


class AccuracyBelowTask(BaseTask):
    type_key = "accuracy_below"
    description_template = "Get below {value}% accuracy"

    @classmethod
    def generate_params(cls):
        return {"value": random.choice(range(50, 75))}

    @classmethod
    def check(cls, score, params):
        return score.score_accuracy <= params["value"]


task_registry: dict[str, type[BaseTask]] = BaseTask._registry
