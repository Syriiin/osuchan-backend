import copy
import random
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, NamedTuple

from django.conf import settings
from django.utils.module_loading import import_string


class GameScore(NamedTuple):
    """
    Score with all fields needed for game logic evaluation.
    Serialised from MinigameScore + Score + Beatmap + annotated
    performance/difficulty totals.
    """

    id: int
    player_id: int
    team_id: int
    score_id: int
    points: float

    score_count_300: int
    score_count_100: int
    score_count_50: int
    score_count_miss: int
    score_best_combo: int
    score_perfect: bool
    score_mods_json: dict
    score_accuracy: float
    score_rank: str
    score_date: datetime

    beatmap_id: int
    beatmap_creator_name: str
    beatmap_status: int

    score_performance_total: float | None = None
    score_difficulty_total: float | None = None


class BaseGame(ABC):
    @property
    @abstractmethod
    def game_type(self) -> str:
        """
        The slug for the game.
        """
        ...

    @property
    @abstractmethod
    def display_name(self) -> str:
        """
        The friendly name for the game.
        """
        ...

    def get_settings(self, data: dict) -> dict:
        """
        Get the valid game settings from raw settings data.
        Settings are any game specific value that can be configured by the host in the lobby phase.
        """
        game_length = int(data.get("game_length", 60 * 60))
        return {"game_length": min(game_length, 60 * 60 * 2)}

    def get_initial_state(self, config: dict) -> dict:
        """
        Get the initial state when starting the game.
        Can be used to seed randomised state, as it will only be run once.
        """
        return {}

    def process_scores(
        self, scores: list[GameScore], config: dict, initial_state: dict
    ) -> dict:
        """
        Pure function. Resolve game state from a list of GameScore objects.
        Returns {state, win_condition_reached, players, teams, scores}.
        """
        return {
            "state": {},
            "win_condition_reached": False,
            "players": {},
            "teams": {},
            "scores": {},
        }


class FirstToN(BaseGame):
    @property
    def game_type(self) -> str:
        return "first_to_n"

    @property
    def display_name(self) -> str:
        return "First to N Scores (test)"

    def get_settings(self, data: dict) -> dict:
        settings = super().get_settings(data)

        settings["scores_to_win"] = int(data.get("scores_to_win", 10))

        return settings

    def get_initial_state(self, config: dict) -> dict:
        return {}

    def process_scores(
        self, scores: list[GameScore], config: dict, initial_state: dict
    ) -> dict:
        """
        First team to reach `scores_to_win` scores wins. Ties are broken by
        which team reached the threshold first (earliest score in iteration
        order).
        """
        scores_to_win = config["scores_to_win"]

        team_points: dict[int, int] = {}
        player_points: dict[int, int] = {}
        win_condition_reached: bool = False

        for game_score in scores:
            team_id = game_score.team_id
            player_id = game_score.player_id

            team_points[team_id] = team_points.get(team_id, 0) + 1
            player_points[player_id] = player_points.get(player_id, 0) + 1

            if team_points[team_id] >= scores_to_win:
                win_condition_reached = True
                break

        return {
            "state": {},
            "win_condition_reached": win_condition_reached,
            "players": {
                player_id: {"points": points, "score_count": points}
                for player_id, points in player_points.items()
            },
            "teams": {
                team_id: {"points": points, "score_count": points}
                for team_id, points in team_points.items()
            },
            "scores": {game_score.id: {"points": 1} for game_score in scores},
        }


class LockoutBingo(BaseGame):
    @staticmethod
    def _check_accuracy_above(score: GameScore, value: float) -> bool:
        return score.score_accuracy >= value

    @staticmethod
    def _check_accuracy_below(score: GameScore, value: float) -> bool:
        return score.score_accuracy <= value

    # TODO: add more tasks
    TASK_DEFINITIONS: dict[str, dict[str, Any]] = {
        "accuracy_above": {
            "description": "Get above {value}% accuracy",
            "generate_params": lambda: {"value": random.choice(range(97, 100))},
            "check": _check_accuracy_above,
        },
        "accuracy_below": {
            "description": "Get below {value}% accuracy",
            "generate_params": lambda: {"value": random.choice(range(50, 75))},
            "check": _check_accuracy_below,
        },
    }

    @staticmethod
    def _check_task(task: dict, score: GameScore) -> bool:
        check = LockoutBingo.TASK_DEFINITIONS[task["type"]]["check"]
        return check(score, task["params"]["value"])

    @property
    def game_type(self) -> str:
        return "lockout_bingo"

    @property
    def display_name(self) -> str:
        return "Lockout Bingo"

    def get_settings(self, data: dict) -> dict:
        settings = super().get_settings(data)

        requested_grid_size = int(data.get("grid_size", 3))
        settings["grid_size"] = (
            requested_grid_size if requested_grid_size in [3, 5, 7] else 3
        )

        return settings

    def get_initial_state(self, config: dict) -> dict:
        grid_size = config["grid_size"]
        total = grid_size * grid_size

        task_type_names = list(self.TASK_DEFINITIONS.keys())
        tasks = []
        for i in range(total):
            type_name = random.choice(task_type_names)
            definition = self.TASK_DEFINITIONS[type_name]
            params = definition["generate_params"]()
            tasks.append(
                {
                    "id": i,
                    "type": type_name,
                    "params": params,
                    "description": definition["description"].format(**params),
                    "row": i // grid_size,
                    "col": i % grid_size,
                    "completed_by_score_id": None,
                    "completed_by_player_id": None,
                    "completed_by_team_id": None,
                }
            )

        return {"tasks": tasks}

    def process_scores(
        self, scores: list[GameScore], config: dict, initial_state: dict
    ) -> dict:
        grid_size = config["grid_size"]
        total = grid_size * grid_size
        win_threshold = total // 2 + 1

        tasks = copy.deepcopy(initial_state["tasks"])

        player_points: dict[int, int] = {}
        player_score_counts: dict[int, int] = {}
        team_points: dict[int, int] = {}
        team_score_counts: dict[int, int] = {}
        score_points: dict[int, int] = {}
        win_condition_reached: bool = False

        for game_score in scores:
            points_earned = 0
            for task in tasks:
                if task["completed_by_score_id"] is not None:
                    continue
                if self._check_task(task, game_score):
                    task["completed_by_score_id"] = game_score.id
                    task["completed_by_player_id"] = game_score.player_id
                    task["completed_by_team_id"] = game_score.team_id
                    points_earned += 1

            if points_earned > 0:
                score_points[game_score.id] = (
                    score_points.get(game_score.id, 0) + points_earned
                )
                player_points[game_score.player_id] = (
                    player_points.get(game_score.player_id, 0) + points_earned
                )
                player_score_counts[game_score.player_id] = (
                    player_score_counts.get(game_score.player_id, 0) + 1
                )
                team_points[game_score.team_id] = (
                    team_points.get(game_score.team_id, 0) + points_earned
                )
                team_score_counts[game_score.team_id] = (
                    team_score_counts.get(game_score.team_id, 0) + 1
                )

                if team_points[game_score.team_id] >= win_threshold:
                    win_condition_reached = True
                    break

        return {
            "state": {"tasks": tasks},
            "win_condition_reached": win_condition_reached,
            "players": {
                player_id: {
                    "points": points,
                    "score_count": player_score_counts.get(player_id, 0),
                }
                for player_id, points in player_points.items()
            },
            "teams": {
                team_id: {
                    "points": points,
                    "score_count": team_score_counts.get(team_id, 0),
                }
                for team_id, points in team_points.items()
            },
            "scores": {
                score_id: {"points": points}
                for score_id, points in score_points.items()
            },
        }


game_registry: dict[str, BaseGame] = {
    name: import_string(path)() for name, path in settings.MINIGAMES.items()
}
