from minigames.games import LockoutBingo
from minigames.games.test_helpers import _game_score


def _task(type, value, row=0, col=0, task_id=0):
    param_keys = {
        "accuracy_above": "min_accuracy",
        "accuracy_below": "max_accuracy",
        "requires_mod": "mod",
        "rank_equals": "rank",
        "combo_above": "min_combo",
    }
    t = {
        "accuracy_above": "Score ≥{}% accuracy",
        "accuracy_below": "Score ≤{}% accuracy",
        "requires_mod": "Play with {}",
        "rank_equals": "Get rank {}",
        "combo_above": "≥{} combo",
    }
    return {
        "id": task_id,
        "type": type,
        "params": {param_keys.get(type, "value"): value},
        "description": t.get(type, type).format(int(value)) if isinstance(value, (int, float)) else t.get(type, type).format(value),
        "row": row,
        "col": col,
        "completed_by_score_id": None,
        "completed_by_player_id": None,
        "completed_by_team_id": None,
    }


MOD_TASKS = ["HD", "HR", "DT", "FL", "SD", "NF", "HT", "NC", "SO"]


def _grid_tasks(grid_size: int):
    """Create a list of tasks using requires_mod with distinct mods so scores never cross-match."""
    return [
        _task("requires_mod", MOD_TASKS[i], row=i // grid_size, col=i % grid_size, task_id=i)
        for i in range(grid_size * grid_size)
    ]


def _score_for_task(task_index: int, team_id: int = 1, player_id: int = 1):
    """Create a score that matches exactly the requires_mod task at task_index."""
    return _game_score(
        id=task_index, player_id=player_id, team_id=team_id,
        score_id=task_index, score_mods_json={MOD_TASKS[task_index]: {}},
    )


class TestLockoutBingo:
    def test_grid_3x3_produces_9_tasks(self):
        state = LockoutBingo().get_initial_state({"grid_size": 3})
        assert len(state["tasks"]) == 9

    def test_grid_5x5_produces_25_tasks(self):
        state = LockoutBingo().get_initial_state({"grid_size": 5})
        assert len(state["tasks"]) == 25

    def test_tasks_have_required_fields(self):
        state = LockoutBingo().get_initial_state({"grid_size": 3})
        for task in state["tasks"]:
            assert "id" in task
            assert "type" in task
            assert "params" in task
            assert "description" in task
            assert "row" in task
            assert "col" in task

    def test_row_col_assigned_correctly(self):
        state = LockoutBingo().get_initial_state({"grid_size": 3})
        for task in state["tasks"]:
            expected_row = task["id"] // 3
            expected_col = task["id"] % 3
            assert task["row"] == expected_row
            assert task["col"] == expected_col

    def test_no_scores_no_changes(self):
        initial = {"tasks": [_task("accuracy_above", 95, task_id=0)]}
        result = LockoutBingo().process_scores([], {"grid_size": 1}, initial)

        assert result["state"]["tasks"][0]["completed_by_score_id"] is None
        assert result["win_condition_reached"] is False
        assert result["players"] == {}
        assert result["teams"] == {}
        assert result["scores"] == {}

    def test_single_task_completes_row_and_wins(self):
        initial = {"tasks": [_task("accuracy_above", 95, task_id=0)]}
        score = _game_score(id=1, player_id=1, team_id=1, score_id=1, score_accuracy=97)
        result = LockoutBingo().process_scores([score], {"grid_size": 1}, initial)

        assert result["state"]["tasks"][0]["completed_by_score_id"] == 1
        assert result["state"]["tasks"][0]["completed_by_player_id"] == 1
        assert result["state"]["tasks"][0]["completed_by_team_id"] == 1
        assert result["win_condition_reached"] is True

    def test_score_matches_accuracy_below_task(self):
        initial = {"tasks": [_task("accuracy_below", 80, task_id=0)]}
        score = _game_score(id=1, player_id=1, team_id=1, score_id=1, score_accuracy=75)
        result = LockoutBingo().process_scores([score], {"grid_size": 1}, initial)

        assert result["state"]["tasks"][0]["completed_by_score_id"] == 1
        assert result["win_condition_reached"] is True

    def test_two_tasks_in_row_completes_line_and_wins(self):
        tasks = [
            _task("accuracy_above", 95, row=0, col=0, task_id=0),
            _task("accuracy_below", 98, row=0, col=1, task_id=1),
        ]
        initial = {"tasks": tasks}
        score = _game_score(id=1, player_id=1, team_id=1, score_id=1, score_accuracy=97)
        result = LockoutBingo().process_scores([score], {"grid_size": 2}, initial)

        assert result["state"]["tasks"][0]["completed_by_score_id"] == 1
        assert result["state"]["tasks"][1]["completed_by_score_id"] == 1
        assert result["scores"][1]["points"] == 2
        assert result["win_condition_reached"] is True

    def test_lockout_prevents_second_score(self):
        initial = {"tasks": [_task("accuracy_above", 95, task_id=0)]}
        scores = [
            _game_score(id=1, player_id=1, team_id=1, score_id=1, score_accuracy=97),
            _game_score(id=2, player_id=2, team_id=2, score_id=2, score_accuracy=98),
        ]
        result = LockoutBingo().process_scores(scores, {"grid_size": 1}, initial)

        assert result["state"]["tasks"][0]["completed_by_score_id"] == 1
        assert result["state"]["tasks"][0]["completed_by_player_id"] == 1
        assert 2 not in result["players"]

    def test_full_row_declares_winner(self):
        tasks = _grid_tasks(3)
        initial = {"tasks": tasks}
        scores = [_score_for_task(i) for i in [0, 1, 2]]
        result = LockoutBingo().process_scores(scores, {"grid_size": 3}, initial)

        assert result["win_condition_reached"] is True

    def test_full_column_declares_winner(self):
        tasks = _grid_tasks(3)
        initial = {"tasks": tasks}
        # Complete tasks 0, 3, 6 — column 0
        scores = [_score_for_task(i) for i in [0, 3, 6]]
        result = LockoutBingo().process_scores(scores, {"grid_size": 3}, initial)

        assert result["win_condition_reached"] is True

    def test_no_winner_without_full_line(self):
        tasks = _grid_tasks(3)
        initial = {"tasks": tasks}
        # Complete tasks 0, 1, 3, 4 — no full row or column
        scores = [_score_for_task(i) for i in [0, 1, 3, 4]]
        result = LockoutBingo().process_scores(scores, {"grid_size": 3}, initial)

        assert result["win_condition_reached"] is False

    def test_deadlock_ends_game_with_most_tasks(self):
        tasks = _grid_tasks(3)
        initial = {"tasks": tasks}
        # Checkerboard: each row and column has tasks from both teams
        # T1: tasks 0 (0,0), 2 (0,2), 4 (1,1), 6 (2,0), 8 (2,2) = 5
        # T2: tasks 1 (0,1), 3 (1,0), 5 (1,2), 7 (2,1) = 4
        scores = [
            _score_for_task(0, team_id=1),
            _score_for_task(1, team_id=2),
            _score_for_task(2, team_id=1),
            _score_for_task(3, team_id=2),
            _score_for_task(4, team_id=1),
            _score_for_task(5, team_id=2),
            _score_for_task(6, team_id=1),
            _score_for_task(7, team_id=2),
            _score_for_task(8, team_id=1),
        ]
        result = LockoutBingo().process_scores(scores, {"grid_size": 3}, initial)

        assert result["win_condition_reached"] is True
        assert result["teams"][1]["points"] == 5
        assert result["teams"][2]["points"] == 4

    def test_one_team_does_not_deadlock(self):
        tasks = _grid_tasks(3)
        initial = {"tasks": tasks}
        # Team 1 completes tasks 0, 1, 2 — full row 0, declares winner
        scores = [_score_for_task(i) for i in [0, 1, 2]]
        result = LockoutBingo().process_scores(scores, {"grid_size": 3}, initial)

        assert result["win_condition_reached"] is True

    def test_accuracy_below_task_does_not_match_high_accuracy(self):
        initial = {"tasks": [_task("accuracy_below", 80, task_id=0)]}
        score = _game_score(id=1, player_id=1, team_id=1, score_id=1, score_accuracy=95)
        result = LockoutBingo().process_scores([score], {"grid_size": 1}, initial)

        assert result["state"]["tasks"][0]["completed_by_score_id"] is None
        assert result["win_condition_reached"] is False

    def test_accuracy_above_task_does_not_match_low_accuracy(self):
        initial = {"tasks": [_task("accuracy_above", 95, task_id=0)]}
        score = _game_score(id=1, player_id=1, team_id=1, score_id=1, score_accuracy=80)
        result = LockoutBingo().process_scores([score], {"grid_size": 1}, initial)

        assert result["state"]["tasks"][0]["completed_by_score_id"] is None
        assert result["win_condition_reached"] is False

    def test_tasks_block_in_separate_rows_no_deadlock(self):
        tasks = _grid_tasks(3)
        initial = {"tasks": tasks}
        # Team 1: tasks 0 (0,0), 3 (1,0)
        # Team 2: tasks 1 (0,1), 4 (1,1)
        # Row 0: team 1+2 → blocked
        # Row 1: team 1+2 → blocked
        # Col 0: only team 1 → possible
        # No deadlock, no winner
        scores = [
            _score_for_task(0, team_id=1),
            _score_for_task(1, team_id=2),
            _score_for_task(3, team_id=1),
            _score_for_task(4, team_id=2),
        ]
        result = LockoutBingo().process_scores(scores, {"grid_size": 3}, initial)

        assert result["win_condition_reached"] is False
