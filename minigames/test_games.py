from datetime import datetime

from minigames.games import FirstToN, GameScore, LockoutBingo


def _game_score(id=1, player_id=1, team_id=1, score_id=1, score_accuracy=0.0):
    """
    Helper to construct a GameScore with sensible defaults.
    """
    return GameScore(
        id=id,
        player_id=player_id,
        team_id=team_id,
        score_id=score_id,
        points=0,
        score_count_300=0,
        score_count_100=0,
        score_count_50=0,
        score_count_miss=0,
        score_best_combo=0,
        score_perfect=False,
        score_mods_json={},
        score_accuracy=score_accuracy,
        score_rank="A",
        score_date=datetime(2026, 1, 1, 12, 0, 0),
        beatmap_id=1,
        beatmap_creator_name="m",
        beatmap_status=1,
    )


class TestFirstToN:
    def test_no_scores_produces_no_winner(self):
        game = FirstToN()
        result = game.process_scores([], {"scores_to_win": 3}, {})

        assert result["win_condition_reached"] is False
        assert result["scores"] == {}

    def test_exact_threshold_declares_winner(self):
        scores = [_game_score(id=i, team_id=1, score_id=i) for i in range(1, 4)]
        result = FirstToN().process_scores(scores, {"scores_to_win": 3}, {})

        assert result["win_condition_reached"] is True
        assert result["teams"][1]["points"] == 3

    def test_below_threshold_no_winner(self):
        scores = [_game_score(id=1, team_id=1), _game_score(id=2, team_id=2)]
        result = FirstToN().process_scores(scores, {"scores_to_win": 3}, {})

        assert result["win_condition_reached"] is False

    def test_multiplayer_team_aggregation(self):
        scores = [
            _game_score(id=1, player_id=1, team_id=1),
            _game_score(id=2, player_id=2, team_id=1),
            _game_score(id=3, player_id=3, team_id=2),
        ]
        result = FirstToN().process_scores(scores, {"scores_to_win": 2}, {})

        assert result["win_condition_reached"] is True
        assert result["players"][1]["points"] == 1
        assert result["players"][2]["points"] == 1
        assert result["teams"][1]["points"] == 2
        assert result["teams"].get(2) is None

    def test_scores_dict_returned(self):
        scores = [_game_score(id=1)]
        result = FirstToN().process_scores(scores, {"scores_to_win": 1}, {})

        assert result["scores"] == {1: {"points": 1}}


def _task(type, value, row=0, col=0, task_id=0):
    """Helper to construct a task dict for testing."""
    t = {
        "accuracy_above": "Score ≥{}% accuracy",
        "accuracy_below": "Score ≤{}% accuracy",
    }
    return {
        "id": task_id,
        "type": type,
        "params": {"value": value},
        "description": t.get(type, type).format(int(value)),
        "row": row,
        "col": col,
        "completed_by_score_id": None,
        "completed_by_player_id": None,
        "completed_by_team_id": None,
    }


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

    def test_score_matches_accuracy_above_task(self):
        initial = {"tasks": [_task("accuracy_above", 95, task_id=0)]}
        score = _game_score(id=1, player_id=1, team_id=1, score_id=1, score_accuracy=97)
        result = LockoutBingo().process_scores([score], {"grid_size": 1}, initial)

        assert result["state"]["tasks"][0]["completed_by_score_id"] == 1
        assert result["state"]["tasks"][0]["completed_by_player_id"] == 1
        assert result["state"]["tasks"][0]["completed_by_team_id"] == 1

    def test_score_matches_accuracy_below_task(self):
        initial = {"tasks": [_task("accuracy_below", 80, task_id=0)]}
        score = _game_score(id=1, player_id=1, team_id=1, score_id=1, score_accuracy=75)
        result = LockoutBingo().process_scores([score], {"grid_size": 1}, initial)

        assert result["state"]["tasks"][0]["completed_by_score_id"] == 1

    def test_score_can_complete_multiple_tasks(self):
        tasks = [
            _task("accuracy_above", 95, row=0, col=0, task_id=0),
            _task("accuracy_below", 98, row=0, col=1, task_id=1),
        ]
        initial = {"tasks": tasks}
        # acc=97 matches both: >=95 and <=98
        score = _game_score(id=1, player_id=1, team_id=1, score_id=1, score_accuracy=97)
        result = LockoutBingo().process_scores([score], {"grid_size": 2}, initial)

        assert result["state"]["tasks"][0]["completed_by_score_id"] == 1
        assert result["state"]["tasks"][1]["completed_by_score_id"] == 1
        assert result["scores"][1]["points"] == 2

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

    def test_winner_at_half_plus_one(self):
        # Each task has a different threshold so a score only matches one
        tasks = [_task("accuracy_above", 90 + i, task_id=i) for i in range(9)]
        initial = {"tasks": tasks}
        scores = [
            _game_score(
                id=i, player_id=1, team_id=1, score_id=i, score_accuracy=90 + i + 0.5
            )
            for i in range(5)  # 9//2 + 1 = 5
        ]
        result = LockoutBingo().process_scores(scores, {"grid_size": 3}, initial)

        assert result["win_condition_reached"] is True
        assert result["teams"][1]["points"] == 5

    def test_below_threshold_no_winner(self):
        tasks = [_task("accuracy_above", 90 + i, task_id=i) for i in range(9)]
        initial = {"tasks": tasks}
        scores = [
            _game_score(
                id=i, player_id=1, team_id=1, score_id=i, score_accuracy=90 + i + 0.5
            )
            for i in range(4)  # 9//2 + 1 = 5, so 4 is not enough
        ]
        result = LockoutBingo().process_scores(scores, {"grid_size": 3}, initial)

        assert result["win_condition_reached"] is False

    def test_accuracy_below_task_does_not_match_high_accuracy(self):
        initial = {"tasks": [_task("accuracy_below", 80, task_id=0)]}
        score = _game_score(id=1, player_id=1, team_id=1, score_id=1, score_accuracy=95)
        result = LockoutBingo().process_scores([score], {"grid_size": 1}, initial)

        assert result["state"]["tasks"][0]["completed_by_score_id"] is None

    def test_accuracy_above_task_does_not_match_low_accuracy(self):
        initial = {"tasks": [_task("accuracy_above", 95, task_id=0)]}
        score = _game_score(id=1, player_id=1, team_id=1, score_id=1, score_accuracy=80)
        result = LockoutBingo().process_scores([score], {"grid_size": 1}, initial)

        assert result["state"]["tasks"][0]["completed_by_score_id"] is None
