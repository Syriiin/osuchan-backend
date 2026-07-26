from minigames.games.base import BaseGame, GameScore


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
