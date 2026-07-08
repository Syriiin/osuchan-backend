from datetime import datetime

from minigames.games import FirstToN, GameScore


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
