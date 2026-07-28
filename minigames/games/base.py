from abc import ABC, abstractmethod
from datetime import datetime
from typing import NamedTuple


class GameScore(NamedTuple):
    id: int
    player_id: int
    team_id: int
    score_id: int
    points: float

    score_score: int
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
    beatmap_title: str
    beatmap_artist: str
    beatmap_difficulty_name: str
    beatmap_approval_date: datetime | None
    beatmap_hitobject_counts: dict

    score_bpm: float
    score_length: float
    score_overall_difficulty: float
    score_approach_rate: float

    score_performance_total: float | None = None
    score_difficulty_total: float | None = None


class Player(NamedTuple):
    id: int
    user_id: int
    team_id: int


class Team(NamedTuple):
    id: int
    name: str


class BaseGame(ABC):
    @property
    @abstractmethod
    def game_type(self) -> str: ...

    @property
    @abstractmethod
    def display_name(self) -> str: ...

    def get_settings(self, data: dict) -> dict:
        game_length = int(data.get("game_length", 60 * 60))
        return {"game_length": min(game_length, 60 * 60 * 2)}

    def get_initial_state(
        self, config: dict, players: list[Player], teams: list[Team], start_time: datetime
    ) -> dict:
        return {}

    def process_scores(
        self, scores: list[GameScore], config: dict, initial_state: dict, current_time: datetime
    ) -> dict:
        return {
            "state": {},
            "win_condition_reached": False,
            "players": {},
            "teams": {},
            "scores": {},
        }
