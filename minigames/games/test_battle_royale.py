from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json

import pytest

from common.osu.enums import Gamemode
from minigames.games import BattleRoyale
from minigames.games.base import MinigameConfigError, Player, Team
from minigames.games.battle_royale import EliminationMode
from minigames.games.test_helpers import _game_score
from profiles.models import Beatmap

_TEST_TIME = datetime(2026, 1, 1, 12, 0, 0)
_SECOND = timedelta(seconds=1)


@pytest.fixture
def br_beatmaps():
    return [
        Beatmap.objects.create(
            id=100,
            set_id=10,
            artist="test artist",
            title="test title 1",
            difficulty_name="test difficulty",
            gamemode=Gamemode.STANDARD,
            status=1,
            creator_name="test creator",
            bpm=180,
            drain_time=556,
            total_time=120,
            max_combo=2843,
            circle_size=4,
            overall_difficulty=6,
            approach_rate=8,
            health_drain=5,
            submission_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            approval_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            last_updated=datetime(2023, 1, 1, tzinfo=timezone.utc),
            hitobject_counts={"circles": 1739, "sliders": 360, "spinners": 1},
            creator_id=1,
        ),
        Beatmap.objects.create(
            id=101,
            set_id=10,
            artist="test artist",
            title="test title 2",
            difficulty_name="test difficulty",
            gamemode=Gamemode.STANDARD,
            status=1,
            creator_name="test creator",
            bpm=180,
            drain_time=556,
            total_time=180,
            max_combo=2843,
            circle_size=4,
            overall_difficulty=6,
            approach_rate=8,
            health_drain=5,
            submission_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            approval_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            last_updated=datetime(2023, 1, 1, tzinfo=timezone.utc),
            hitobject_counts={"circles": 1739, "sliders": 360, "spinners": 1},
            creator_id=1,
        ),
        Beatmap.objects.create(
            id=102,
            set_id=10,
            artist="test artist",
            title="test title 3",
            difficulty_name="test difficulty",
            gamemode=Gamemode.STANDARD,
            status=1,
            creator_name="test creator",
            bpm=180,
            drain_time=556,
            total_time=240,
            max_combo=2843,
            circle_size=4,
            overall_difficulty=6,
            approach_rate=8,
            health_drain=5,
            submission_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            approval_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            last_updated=datetime(2023, 1, 1, tzinfo=timezone.utc),
            hitobject_counts={"circles": 1739, "sliders": 360, "spinners": 1},
            creator_id=1,
        ),
    ]

FOUR_TEAMS_CONFIG = {
    "beatmaps": [
        {"beatmap_id": 100, "allowed_mods": []},
        {"beatmap_id": 101, "allowed_mods": []},
    ],
    "play_start_window": 30,
    "submission_buffer": 30,
    "intermission": 60,
    "elimination_mode": EliminationMode.MANUAL,
    "teams_remaining": [3, 1],
}


def _make(state, **overrides):
    return {**state, **overrides}


def _round(beatmap_id, target_teams, round_start, cutoff, **kw):
    return _make(
        {
            "beatmap_id": beatmap_id,
            "allowed_mods": [],
            "target_teams": target_teams,
            "round_start": (round_start if isinstance(round_start, str) else round_start.isoformat()),
            "cutoff_time": (cutoff if isinstance(cutoff, str) else cutoff.isoformat()),
            "player_scores": {},
            "team_scores": {},
            "eliminated_team_ids": [],
        },
        **kw,
    )


def _initial_state(rounds, team_ids, team_player_map):
    return {
        "rounds": deepcopy(rounds),
        "active_team_ids": list(team_ids),
        "eliminated_team_ids": [],
        "team_player_map": team_player_map,
    }


def _score(id, player_id, team_id, beatmap_id, score_date, score_score=1_000_000, **kw):
    return _game_score(
        id=id,
        player_id=player_id,
        team_id=team_id,
        score_id=id,
        score_score=score_score,
        beatmap_id=beatmap_id,
        score_date=score_date,
        **kw,
    )


@pytest.mark.django_db
class TestGetSettings:
    def test_no_beatmaps_and_no_available_maps_raises(self):
        with pytest.raises(MinigameConfigError):
            BattleRoyale().get_settings({})

        with pytest.raises(MinigameConfigError):
            BattleRoyale().get_settings({"beatmaps": []})

    def test_no_beatmaps_picks_random_beatmaps(self, br_beatmaps):
        result = BattleRoyale().get_settings({})
        assert len(result["beatmaps"]) == 3
        assert {beatmap["beatmap_id"] for beatmap in result["beatmaps"]} <= {100, 101, 102}
        assert all(beatmap["allowed_mods"] == [] for beatmap in result["beatmaps"])

    def test_random_beatmaps_filtered_by_gamemode(self, br_beatmaps):
        with pytest.raises(MinigameConfigError):
            BattleRoyale().get_settings({}, Gamemode.TAIKO)

    def test_unknown_beatmap_raises(self):
        with pytest.raises(MinigameConfigError):
            BattleRoyale().get_settings({"beatmaps": [{"beatmap_id": 1}]})

    def test_invalid_beatmap_id_raises(self):
        with pytest.raises(MinigameConfigError):
            BattleRoyale().get_settings({"beatmaps": [{"beatmap_id": "abc"}]})

    def test_valid_beatmaps_accepted(self, br_beatmaps):
        result = BattleRoyale().get_settings(
            {"beatmaps": [{"beatmap_id": 100}, {"beatmap_id": 101}]}
        )
        assert result["beatmaps"] == [
            {"beatmap_id": 100, "allowed_mods": []},
            {"beatmap_id": 101, "allowed_mods": []},
        ]

    def test_game_length_matches_round_timings(self, br_beatmaps):
        result = BattleRoyale().get_settings(
            {
                "beatmaps": [{"beatmap_id": 100}, {"beatmap_id": 101}],
                "play_start_window": 30,
                "submission_buffer": 30,
                "intermission": 60,
            }
        )
        assert result["game_length"] == (30 + 120 + 30) + (30 + 180 + 30) + 60

    def test_game_length_override_respected(self, br_beatmaps):
        result = BattleRoyale().get_settings(
            {"beatmaps": [{"beatmap_id": 100}], "game_length": 123}
        )
        assert result["game_length"] == 123

    def test_play_start_window_clamped(self, br_beatmaps):
        result = BattleRoyale().get_settings(
            {
                "beatmaps": [{"beatmap_id": 100}],
                "play_start_window": 5,
            }
        )
        assert result["play_start_window"] == 10
        result = BattleRoyale().get_settings(
            {
                "beatmaps": [{"beatmap_id": 100}],
                "play_start_window": 200,
            }
        )
        assert result["play_start_window"] == 120

    def test_manual_mode_stores_teams_remaining(self, br_beatmaps):
        result = BattleRoyale().get_settings({
            "beatmaps": [{"beatmap_id": 100}, {"beatmap_id": 101}],
            "elimination_mode": EliminationMode.MANUAL,
            "teams_remaining": [3, 1],
        })
        assert result["elimination_mode"] == EliminationMode.MANUAL
        assert result["teams_remaining"] == [3, 1]

    def test_manual_mode_fallback_on_mismatch(self, br_beatmaps):
        result = BattleRoyale().get_settings({
            "beatmaps": [{"beatmap_id": 100}, {"beatmap_id": 101}],
            "elimination_mode": EliminationMode.MANUAL,
            "teams_remaining": [3],
        })
        assert result["elimination_mode"] == EliminationMode.AUTO


class TestAutoTargets:
    def test_single_round(self):
        targets = BattleRoyale._compute_auto_targets(8, 1)
        assert targets == [1]

    def test_two_rounds(self):
        targets = BattleRoyale._compute_auto_targets(8, 2)
        assert targets == [2, 1]

    def test_five_rounds(self):
        targets = BattleRoyale._compute_auto_targets(16, 5)
        assert targets == [11, 7, 4, 2, 1]

    def test_large_field_monotonic_eliminations(self):
        targets = BattleRoyale._compute_auto_targets(100, 15)
        eliminations = [100 - targets[0]] + [
            targets[i - 1] - targets[i] for i in range(1, len(targets))
        ]
        assert eliminations == sorted(eliminations, reverse=True)
        assert min(eliminations) >= 1
        assert sum(eliminations) == 99

    def test_large_field_smooth_ramp_down(self):
        targets = BattleRoyale._compute_auto_targets(100, 15)
        assert targets == [88, 77, 66, 56, 47, 39, 32, 25, 19, 14, 10, 7, 4, 2, 1]

    def test_more_rounds_than_teams_warmups(self):
        targets = BattleRoyale._compute_auto_targets(4, 6)
        assert targets == [4, 4, 4, 3, 2, 1]

    def test_zero_rounds(self):
        assert BattleRoyale._compute_auto_targets(10, 0) == []


class TestGetInitialState:
    @pytest.mark.django_db
    def test_round_count_matches_beatmaps(self, br_beatmaps):
        state = BattleRoyale().get_initial_state(
            FOUR_TEAMS_CONFIG,
            [Player(id=1, user_id=1, team_id=1)],
            [Team(id=1, name="A")],
            _TEST_TIME,
        )
        assert len(state["rounds"]) == 2

    @pytest.mark.django_db
    def test_team_player_map(self, br_beatmaps):
        players = [
            Player(id=1, user_id=1, team_id=1),
            Player(id=2, user_id=2, team_id=1),
            Player(id=3, user_id=3, team_id=2),
        ]
        teams = [Team(id=1, name="A"), Team(id=2, name="B")]
        state = BattleRoyale().get_initial_state(
            FOUR_TEAMS_CONFIG,
            players, teams, _TEST_TIME,
        )
        assert state["team_player_map"] == {1: [1, 2], 2: [3]}

    @pytest.mark.django_db
    def test_active_teams_all_teams(self, br_beatmaps):
        teams = [Team(id=1, name="A"), Team(id=2, name="B")]
        state = BattleRoyale().get_initial_state(
            FOUR_TEAMS_CONFIG,
            [Player(id=1, user_id=1, team_id=1)],
            teams, _TEST_TIME,
        )
        assert state["active_team_ids"] == [1, 2]

    @pytest.mark.django_db
    def test_round_timestamps(self, br_beatmaps):
        state = BattleRoyale().get_initial_state(
            FOUR_TEAMS_CONFIG,
            [Player(id=1, user_id=1, team_id=1)],
            [Team(id=1, name="A")],
            _TEST_TIME,
        )
        r1 = state["rounds"][0]
        assert r1["round_start"] == _TEST_TIME.isoformat()

        r1_start = datetime.fromisoformat(r1["round_start"])
        r1_cutoff = datetime.fromisoformat(r1["cutoff_time"])
        assert r1_cutoff == r1_start + timedelta(seconds=30 + 120 + 30)

        r2_start = datetime.fromisoformat(state["rounds"][1]["round_start"])
        assert r2_start == r1_cutoff + timedelta(seconds=60)

    @pytest.mark.django_db
    def test_last_round_cutoff_matches_game_length(self, br_beatmaps):
        config = BattleRoyale().get_settings(
            {
                "beatmaps": [{"beatmap_id": 100}, {"beatmap_id": 101}],
                "play_start_window": 30,
                "submission_buffer": 30,
                "intermission": 60,
            }
        )
        state = BattleRoyale().get_initial_state(
            config,
            [Player(id=1, user_id=1, team_id=1)],
            [Team(id=1, name="A")],
            _TEST_TIME,
        )

        last_cutoff = datetime.fromisoformat(state["rounds"][-1]["cutoff_time"])
        assert last_cutoff == _TEST_TIME + timedelta(seconds=config["game_length"])


class TestProcessScores:
    def _config(self, **overrides):
        return {**FOUR_TEAMS_CONFIG, **overrides}

    def test_no_scores_all_eliminated(self):
        r1 = _round(100, 2, _TEST_TIME, _TEST_TIME + _SECOND)
        state = _initial_state([r1], [1, 2, 3, 4], {1: [1], 2: [2], 3: [3], 4: [4]})

        result = BattleRoyale().process_scores([], self._config(), state, _TEST_TIME + timedelta(seconds=10))

        assert result["state"]["active_team_ids"] == [3, 4]
        assert result["state"]["eliminated_team_ids"] == [1, 2]

    def test_json_round_tripped_initial_state_uses_int_ids(self):
        r1 = _round(100, 2, _TEST_TIME, _TEST_TIME + _SECOND)
        state = _initial_state([r1], [1, 2, 3, 4], {1: [1], 2: [2], 3: [3], 4: [4]})
        state = json.loads(json.dumps(state))

        result = BattleRoyale().process_scores([], self._config(), state, _TEST_TIME + timedelta(seconds=10))

        assert result["teams"].keys() == {1, 2, 3, 4}
        assert result["players"].keys() == {1, 2, 3, 4}
        assert result["state"]["active_team_ids"] == [3, 4]

    def test_highest_score_teams_survive(self):
        r1 = _round(100, 2, _TEST_TIME, _TEST_TIME + _SECOND)
        state = _initial_state([r1], [1, 2, 3, 4], {1: [1], 2: [2], 3: [3], 4: [4]})
        scores = [
            _score(1, 1, 1, 100, _TEST_TIME, score_score=1_000_000),
            _score(2, 2, 2, 100, _TEST_TIME, score_score=900_000),
            _score(3, 3, 3, 100, _TEST_TIME, score_score=500_000),
        ]

        result = BattleRoyale().process_scores(scores, self._config(), state, _TEST_TIME + timedelta(seconds=10))

        assert result["state"]["active_team_ids"] == [1, 2]
        assert 3 in result["state"]["eliminated_team_ids"]
        assert 4 in result["state"]["eliminated_team_ids"]

    def test_first_score_per_player(self):
        r1 = _round(100, 2, _TEST_TIME, _TEST_TIME + timedelta(seconds=60))
        state = _initial_state([r1], [1, 2, 3], {1: [1], 2: [2], 3: [3]})
        scores = [
            _score(1, 1, 1, 100, _TEST_TIME + _SECOND, score_score=100_000),
            _score(2, 1, 1, 100, _TEST_TIME + timedelta(seconds=10), score_score=2_000_000),
            _score(3, 2, 2, 100, _TEST_TIME + _SECOND, score_score=150_000),
            _score(4, 3, 3, 100, _TEST_TIME + _SECOND, score_score=120_000),
        ]

        result = BattleRoyale().process_scores(scores, self._config(), state, _TEST_TIME + timedelta(seconds=120))
        # Team 1's first score (100k) is used, not the 2M follow-up
        # Team 1 loses despite having a later 2M score
        assert 1 in result["state"]["eliminated_team_ids"]
        assert result["state"]["active_team_ids"] == [2, 3]
        assert result["scores"] == {
            1: {"points": 100_000},
            3: {"points": 150_000},
            4: {"points": 120_000},
        }

    def test_out_of_order_scores_processed_chronologically(self):
        r1 = _round(100, 2, _TEST_TIME, _TEST_TIME + timedelta(seconds=60))
        state = _initial_state([r1], [1, 2, 3], {1: [1], 2: [2], 3: [3]})
        scores = [
            _score(1, 1, 1, 100, _TEST_TIME + timedelta(seconds=10), score_score=2_000_000),
            _score(2, 2, 2, 100, _TEST_TIME + timedelta(seconds=2), score_score=150_000),
            _score(3, 3, 3, 100, _TEST_TIME + timedelta(seconds=2), score_score=120_000),
            _score(4, 1, 1, 100, _TEST_TIME + _SECOND, score_score=100_000),
        ]

        result = BattleRoyale().process_scores(scores, self._config(), state, _TEST_TIME + timedelta(seconds=120))
        # Team 1's 2M score is listed first, but the earlier 100k is used
        assert 1 in result["state"]["eliminated_team_ids"]
        assert result["state"]["active_team_ids"] == [2, 3]

    def test_pre_cutoff_scores_assigned_no_elimination(self):
        r1 = _round(100, 2, _TEST_TIME, _TEST_TIME + timedelta(seconds=60))
        state = _initial_state([r1], [1, 2, 3], {1: [1], 2: [2], 3: [3]})
        scores = [
            _score(1, 3, 3, 100, _TEST_TIME + _SECOND, score_score=100_000),
        ]

        result = BattleRoyale().process_scores(scores, self._config(), state, _TEST_TIME + timedelta(seconds=30))

        assert result["state"]["active_team_ids"] == [1, 2, 3]
        assert result["state"]["rounds"][0]["player_scores"] == {3: 1}
        assert result["state"]["rounds"][0]["team_scores"] == {3: 100_000}
        assert result["win_condition_reached"] is False

    def test_team_scores_live_before_cutoff_no_elimination(self):
        r1 = _round(100, 2, _TEST_TIME, _TEST_TIME + timedelta(seconds=60))
        state = _initial_state([r1], [1, 2, 3], {1: [1], 2: [2], 3: [3]})
        scores = [
            _score(1, 1, 1, 100, _TEST_TIME + _SECOND, score_score=300_000),
            _score(2, 2, 2, 100, _TEST_TIME + _SECOND, score_score=400_000),
            _score(3, 3, 3, 100, _TEST_TIME + _SECOND, score_score=500_000),
        ]

        result = BattleRoyale().process_scores(scores, self._config(), state, _TEST_TIME + timedelta(seconds=30))

        assert result["state"]["rounds"][0]["team_scores"] == {
            1: 300_000,
            2: 400_000,
            3: 500_000,
        }
        assert result["state"]["active_team_ids"] == [1, 2, 3]
        assert result["state"]["eliminated_team_ids"] == []
        assert result["teams"][1]["points"] == 0
        assert result["teams"][2]["points"] == 0
        assert result["teams"][3]["points"] == 0

    def test_multi_round_progressive_elimination(self):
        r1 = _round(100, 3, _TEST_TIME, _TEST_TIME + _SECOND)
        r2 = _round(101, 1, _TEST_TIME + timedelta(seconds=60), _TEST_TIME + timedelta(seconds=61))
        state = _initial_state([r1, r2], [1, 2, 3, 4], {1: [1], 2: [2], 3: [3], 4: [4]})
        scores = [
            _score(1, 1, 1, 100, _TEST_TIME, score_score=1_000_000),
            _score(2, 2, 2, 100, _TEST_TIME, score_score=900_000),
            _score(3, 3, 3, 100, _TEST_TIME, score_score=800_000),
            _score(4, 4, 4, 100, _TEST_TIME, score_score=100_000),
            _score(5, 1, 1, 101, _TEST_TIME + timedelta(seconds=60), score_score=500_000),
            _score(6, 2, 2, 101, _TEST_TIME + timedelta(seconds=60), score_score=400_000),
        ]

        result = BattleRoyale().process_scores(
            scores, self._config(), state, _TEST_TIME + timedelta(seconds=120)
        )

        # Round 1: 4 teams, target 3, eliminate team 4
        # Round 2: 3 teams (1,2,3), target 1, eliminate teams 2 and 3
        assert result["state"]["active_team_ids"] == [1]
        assert result["win_condition_reached"] is True

    def test_win_condition_when_one_team_remains(self):
        r1 = _round(100, 1, _TEST_TIME, _TEST_TIME + _SECOND)
        state = _initial_state([r1], [1, 2], {1: [1], 2: [2]})
        scores = [
            _score(1, 1, 1, 100, _TEST_TIME, score_score=1_000_000),
        ]

        result = BattleRoyale().process_scores(scores, self._config(), state, _TEST_TIME + timedelta(seconds=10))

        assert result["win_condition_reached"] is True
        assert result["state"]["active_team_ids"] == [1]

    def test_beatmap_id_filter(self):
        r1 = _round(100, 2, _TEST_TIME, _TEST_TIME + _SECOND)
        state = _initial_state([r1], [1, 2, 3], {1: [1], 2: [2], 3: [3]})
        scores = [
            _score(1, 1, 1, 200, _TEST_TIME, score_score=1_000_000),
            _score(2, 2, 2, 100, _TEST_TIME, score_score=100_000),
        ]

        result = BattleRoyale().process_scores(scores, self._config(), state, _TEST_TIME + timedelta(seconds=10))

        assert 1 in result["state"]["eliminated_team_ids"]
        assert result["state"]["active_team_ids"] == [2, 3]

    def test_score_outside_time_window_ignored(self):
        r1 = _round(100, 2, _TEST_TIME, _TEST_TIME + timedelta(seconds=10))
        state = _initial_state([r1], [1, 2, 3], {1: [1], 2: [2], 3: [3]})
        scores = [
            _score(1, 1, 1, 100, _TEST_TIME + timedelta(seconds=20), score_score=1_000_000),
            _score(2, 2, 2, 100, _TEST_TIME - _SECOND, score_score=1_000_000),
        ]

        result = BattleRoyale().process_scores(scores, self._config(), state, _TEST_TIME + timedelta(seconds=30))
        # No valid scores: all teams tied at -1 → lowest team_id eliminated
        assert result["state"]["active_team_ids"] == [2, 3]
        assert result["state"]["eliminated_team_ids"] == [1]

    def test_team_with_multiple_players(self):
        r1 = _round(100, 1, _TEST_TIME, _TEST_TIME + _SECOND)
        state = _initial_state([r1], [1, 2, 3], {1: [1, 2], 2: [3], 3: [4]})
        scores = [
            _score(1, 1, 1, 100, _TEST_TIME, score_score=300_000),
            _score(2, 2, 1, 100, _TEST_TIME, score_score=200_000),
            _score(3, 3, 2, 100, _TEST_TIME, score_score=400_000),
            _score(4, 4, 3, 100, _TEST_TIME, score_score=100_000),
        ]

        result = BattleRoyale().process_scores(scores, self._config(), state, _TEST_TIME + timedelta(seconds=10))
        # Team 1 has 2 players = 500k total
        # Team 2 has 1 player = 400k
        # Team 3 has 1 player = 100k
        # Target 1 team → only team 1 survives
        assert result["state"]["active_team_ids"] == [1]

    def test_points_one_per_round_survived(self):
        r1 = _round(100, 2, _TEST_TIME, _TEST_TIME + _SECOND)
        r2 = _round(101, 1, _TEST_TIME + timedelta(seconds=60), _TEST_TIME + timedelta(seconds=61))
        state = _initial_state([r1, r2], [1, 2, 3], {1: [1], 2: [2], 3: [3]})
        scores = [
            _score(1, 1, 1, 100, _TEST_TIME, score_score=1_000_000),
            _score(2, 2, 2, 100, _TEST_TIME, score_score=900_000),
            _score(3, 3, 3, 100, _TEST_TIME, score_score=800_000),
            _score(4, 1, 1, 101, _TEST_TIME + timedelta(seconds=60), score_score=500_000),
            _score(5, 2, 2, 101, _TEST_TIME + timedelta(seconds=60), score_score=400_000),
        ]

        result = BattleRoyale().process_scores(
            scores, self._config(), state, _TEST_TIME + timedelta(seconds=120)
        )

        assert result["teams"][1]["points"] == 2
        assert result["teams"][2]["points"] == 1
        assert result["teams"][3]["points"] == 0
        assert result["players"][1]["points"] == 2
        assert result["players"][2]["points"] == 1
        assert result["players"][3]["points"] == 0

    def test_two_team_final_round_win_condition(self):
        r1 = _round(100, 1, _TEST_TIME, _TEST_TIME + _SECOND)
        state = _initial_state([r1], [1, 2], {1: [1], 2: [2]})
        scores = [
            _score(1, 1, 1, 100, _TEST_TIME, score_score=100_000),
            _score(2, 2, 2, 100, _TEST_TIME, score_score=50_000),
        ]

        result = BattleRoyale().process_scores(scores, self._config(), state, _TEST_TIME + timedelta(seconds=10))

        assert result["win_condition_reached"] is True
        assert result["state"]["active_team_ids"] == [1]
        assert result["teams"][1]["points"] == 1
        assert result["teams"][2]["points"] == 0

    def test_no_teams_remaining_no_winner(self):
        r1 = _round(100, 0, _TEST_TIME, _TEST_TIME + _SECOND)
        state = _initial_state([r1], [1], {1: [1]})

        result = BattleRoyale().process_scores([], self._config(), state, _TEST_TIME + timedelta(seconds=10))

        assert result["win_condition_reached"] is True
        assert result["state"]["active_team_ids"] == []

    def test_idempotent_replay(self):
        r1 = _round(100, 2, _TEST_TIME, _TEST_TIME + _SECOND)
        state = _initial_state([r1], [1, 2, 3, 4], {1: [1], 2: [2], 3: [3], 4: [4]})
        scores = [
            _score(1, 1, 1, 100, _TEST_TIME, score_score=1_000_000),
            _score(2, 2, 2, 100, _TEST_TIME, score_score=900_000),
            _score(3, 3, 3, 100, _TEST_TIME, score_score=800_000),
            _score(4, 4, 4, 100, _TEST_TIME, score_score=100_000),
        ]

        first = BattleRoyale().process_scores(scores, self._config(), deepcopy(state), _TEST_TIME + timedelta(seconds=10))
        second = BattleRoyale().process_scores(scores, self._config(), deepcopy(state), _TEST_TIME + timedelta(seconds=10))

        assert first["state"]["active_team_ids"] == second["state"]["active_team_ids"]
        assert first["win_condition_reached"] == second["win_condition_reached"]
        assert first["teams"] == second["teams"]

    def test_late_score_changes_outcome(self):
        r1 = _round(100, 1, _TEST_TIME, _TEST_TIME + timedelta(seconds=60))
        state = _initial_state([r1], [1, 2], {1: [1], 2: [2]})

        early_scores = [
            _score(1, 1, 1, 100, _TEST_TIME + _SECOND, score_score=100_000),
        ]
        late_scores = [
            _score(1, 1, 1, 100, _TEST_TIME + _SECOND, score_score=100_000),
            _score(2, 2, 2, 100, _TEST_TIME + timedelta(seconds=5), score_score=200_000),
        ]

        future = _TEST_TIME + timedelta(seconds=120)
        early_result = BattleRoyale().process_scores(early_scores, self._config(), deepcopy(state), future)
        late_result = BattleRoyale().process_scores(late_scores, self._config(), deepcopy(state), future)

        assert early_result["state"]["active_team_ids"] == [1]
        assert late_result["state"]["active_team_ids"] == [2]
