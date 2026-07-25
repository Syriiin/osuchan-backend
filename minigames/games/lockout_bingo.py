import copy
import random

from minigames.games.base import BaseGame, GameScore
from minigames.games.tasks import task_registry


class LockoutBingo(BaseGame):
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

        task_type_names = list(task_registry.keys())
        tasks = []
        for i in range(total):
            type_name = random.choice(task_type_names)
            task_cls = task_registry[type_name]
            params = task_cls.generate_params()
            tasks.append(
                {
                    "id": i,
                    "type": type_name,
                    "params": params,
                    "description": task_cls.get_description(params),
                    "row": i // grid_size,
                    "col": i % grid_size,
                    "completed_by_score_id": None,
                    "completed_by_player_id": None,
                    "completed_by_team_id": None,
                }
            )

        return {"tasks": tasks}

    @staticmethod
    def _line_is_possible(tasks_in_line: list[dict]) -> bool:
        team_ids = {
            t["completed_by_team_id"]
            for t in tasks_in_line
            if t["completed_by_team_id"] is not None
        }
        return len(team_ids) <= 1

    @staticmethod
    def _line_completed_by(tasks_in_line: list[dict]) -> int | None:
        if not all(t["completed_by_team_id"] is not None for t in tasks_in_line):
            return None
        team_ids = {t["completed_by_team_id"] for t in tasks_in_line}
        return team_ids.pop() if len(team_ids) == 1 else None

    @staticmethod
    def _line_completed(tasks: list[dict], grid_size: int) -> bool:
        for row in range(grid_size):
            row_tasks = [t for t in tasks if t["row"] == row]
            if LockoutBingo._line_completed_by(row_tasks) is not None:
                return True
        for col in range(grid_size):
            col_tasks = [t for t in tasks if t["col"] == col]
            if LockoutBingo._line_completed_by(col_tasks) is not None:
                return True
        return False

    @staticmethod
    def _check_deadlock(tasks: list[dict], grid_size: int) -> bool:
        for row in range(grid_size):
            row_tasks = [t for t in tasks if t["row"] == row]
            if LockoutBingo._line_is_possible(row_tasks):
                return False
        for col in range(grid_size):
            col_tasks = [t for t in tasks if t["col"] == col]
            if LockoutBingo._line_is_possible(col_tasks):
                return False
        return True

    def process_scores(
        self, scores: list[GameScore], config: dict, initial_state: dict
    ) -> dict:
        grid_size = config["grid_size"]

        tasks = copy.deepcopy(initial_state["tasks"])

        player_points: dict[int, int] = {}
        player_score_counts: dict[int, int] = {}
        team_points: dict[int, int] = {}
        team_score_counts: dict[int, int] = {}
        score_points: dict[int, int] = {}

        win_condition_reached = False

        for game_score in scores:
            points_earned = 0
            for task in tasks:
                if task["completed_by_score_id"] is not None:
                    continue
                if task_registry[task["type"]].check(game_score, task["params"]):
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

                if self._line_completed(tasks, grid_size):
                    win_condition_reached = True
                    break

        if not win_condition_reached:
            win_condition_reached = self._check_deadlock(tasks, grid_size)

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
