import copy
import enum
from datetime import datetime, timedelta

from common.osu.enums import BeatmapStatus, Gamemode
from minigames.games.base import BaseGame, GameScore, MinigameConfigError, Player, Team
from profiles.models import Beatmap


class EliminationMode(enum.StrEnum):
    AUTO = "auto"
    MANUAL = "manual"


class BattleRoyale(BaseGame):
    """Elimination-style minigame where teams are removed round by round."""

    @property
    def game_type(self) -> str:
        return "battle_royale"

    @property
    def display_name(self) -> str:
        return "Battle Royale"

    def get_settings(self, data: dict, gamemode: Gamemode | None = None) -> dict:
        beatmaps = data.get("beatmaps", [])
        if not isinstance(beatmaps, list) or len(beatmaps) == 0:
            beatmaps = self._get_random_beatmaps(gamemode)

        beatmap_ids = []
        for beatmap in beatmaps:
            try:
                beatmap_id = int(beatmap["beatmap_id"])
            except KeyError, TypeError, ValueError:
                raise MinigameConfigError("Each beatmap must have a valid beatmap_id.")

            if beatmap_id <= 0:
                raise MinigameConfigError("Each beatmap must have a valid beatmap_id.")

            beatmap_ids.append(beatmap_id)

        beatmap_lengths = {
            beatmap.id: beatmap.total_time
            for beatmap in Beatmap.objects.filter(id__in=beatmap_ids).only(
                "id", "total_time"
            )
        }
        missing_beatmap_ids = sorted(set(beatmap_ids) - set(beatmap_lengths))
        if missing_beatmap_ids:
            raise MinigameConfigError(
                "Unknown beatmap(s): "
                + ", ".join(str(beatmap_id) for beatmap_id in missing_beatmap_ids)
                + "."
            )

        settings = {
            "beatmaps": [
                {
                    "beatmap_id": int(beatmap["beatmap_id"]),
                    "allowed_mods": [
                        str(mod) for mod in beatmap.get("allowed_mods", [])
                    ],
                }
                for beatmap in beatmaps
            ],
            "play_start_window": max(
                10, min(120, int(data.get("play_start_window", 30)))
            ),
            "submission_buffer": max(
                10, min(120, int(data.get("submission_buffer", 30)))
            ),
            "intermission": max(10, min(300, int(data.get("intermission", 60)))),
        }

        mode_raw = data.get("elimination_mode", EliminationMode.AUTO)
        try:
            mode = EliminationMode(mode_raw)
        except ValueError:
            mode = EliminationMode.AUTO
        settings["elimination_mode"] = mode

        if mode is EliminationMode.MANUAL:
            survivors = data.get("teams_remaining", [])
            if isinstance(survivors, list) and len(survivors) == len(beatmaps):
                settings["teams_remaining"] = [int(survivor) for survivor in survivors]
            else:
                settings["elimination_mode"] = EliminationMode.AUTO

        # derive game length from the actual beatmap lengths so the end time
        # matches the final round's cutoff time; rounds each take play window +
        # map length + submission buffer, with an intermission in between
        rounds_length = sum(
            settings["play_start_window"]
            + beatmap_lengths[beatmap_id]
            + settings["submission_buffer"]
            for beatmap_id in beatmap_ids
        )
        intermissions_length = (len(beatmap_ids) - 1) * settings["intermission"]

        settings["game_length"] = min(
            int(data.get("game_length", rounds_length + intermissions_length)),
            60 * 60 * 4,
        )

        return settings

    @staticmethod
    def _get_random_beatmaps(gamemode: Gamemode | None) -> list[dict]:
        beatmap_ids = list(
            Beatmap.objects.filter(
                gamemode=gamemode if gamemode is not None else Gamemode.STANDARD,
                status__in=[
                    BeatmapStatus.RANKED,
                    BeatmapStatus.APPROVED,
                    BeatmapStatus.LOVED,
                ],
            )
            .order_by("?")
            .values_list("id", flat=True)[:3]
        )
        if len(beatmap_ids) == 0:
            raise MinigameConfigError("At least one beatmap is required.")
        return [
            {"beatmap_id": beatmap_id, "allowed_mods": []} for beatmap_id in beatmap_ids
        ]

    def get_initial_state(
        self,
        config: dict,
        players: list[Player],
        teams: list[Team],
        start_time: datetime,
    ) -> dict:
        beatmap_lengths = {
            beatmap.id: beatmap.total_time
            for beatmap in Beatmap.objects.filter(
                id__in=[
                    beatmap_config["beatmap_id"]
                    for beatmap_config in config["beatmaps"]
                ]
            ).only("id", "total_time")
        }

        team_player_map: dict[int, list[int]] = {}
        for player in players:
            team_player_map.setdefault(player.team_id, []).append(player.id)

        team_count = len(teams)
        round_count = len(config["beatmaps"])

        if config["elimination_mode"] == EliminationMode.MANUAL:
            team_targets = config.get("teams_remaining", [])
        else:
            team_targets = self._compute_auto_targets(team_count, round_count)

        rounds = []
        cursor = start_time
        for i, beatmap in enumerate(config["beatmaps"]):
            beatmap_length = beatmap_lengths.get(beatmap["beatmap_id"], 180)

            round_start = cursor
            play_deadline = round_start + timedelta(seconds=config["play_start_window"])
            cutoff_time = play_deadline + timedelta(
                seconds=beatmap_length + config["submission_buffer"]
            )

            rounds.append(
                {
                    "beatmap_id": beatmap["beatmap_id"],
                    "allowed_mods": beatmap["allowed_mods"],
                    "target_teams": team_targets[i],
                    "round_start": round_start.isoformat(),
                    "cutoff_time": cutoff_time.isoformat(),
                    "player_scores": {},
                    "team_scores": {},
                    "eliminated_team_ids": [],
                }
            )

            cursor = cutoff_time + timedelta(seconds=config["intermission"])

        return {
            "rounds": rounds,
            "active_team_ids": [team.id for team in teams],
            "eliminated_team_ids": [],
            "team_player_map": team_player_map,
        }

    @staticmethod
    def _compute_auto_targets(team_count: int, round_count: int) -> list[int]:
        if round_count == 0:
            return []

        total_eliminations = team_count - 1
        active_rounds = min(round_count, total_eliminations)
        warmup_rounds = round_count - active_rounds

        if active_rounds == 0:
            return [team_count] * round_count

        if active_rounds == 1:
            eliminations = [total_eliminations]
        else:
            step = (
                2
                * (total_eliminations - active_rounds)
                / (active_rounds * (active_rounds - 1))
            )
            eliminations = [
                round(1 + step * (active_rounds - 1 - round_index))
                for round_index in range(active_rounds)
            ]
            eliminations = BattleRoyale._adjust_eliminations(
                eliminations, total_eliminations - sum(eliminations)
            )

        targets = []
        survivors = team_count
        for _ in range(warmup_rounds):
            targets.append(survivors)
        for elimination_count in eliminations:
            survivors -= elimination_count
            targets.append(survivors)
        return targets

    @staticmethod
    def _adjust_eliminations(eliminations: list[int], residual: int) -> list[int]:
        index = 0
        while residual != 0 and index < len(eliminations):
            lower_bound = (
                eliminations[index + 1] if index + 1 < len(eliminations) else 1
            )
            if residual > 0:
                adjustment = residual
            else:
                adjustment = -min(-residual, eliminations[index] - lower_bound)
            eliminations[index] += adjustment
            residual -= adjustment
            index += 1
        return eliminations

    def process_scores(
        self,
        scores: list[GameScore],
        config: dict,
        initial_state: dict,
        current_time: datetime,
    ) -> dict:
        scores = sorted(scores, key=lambda score: (score.score_date, score.id))
        rounds = copy.deepcopy(initial_state["rounds"])
        active_team_ids = {int(team_id) for team_id in initial_state["active_team_ids"]}
        team_player_map: dict[int, list[int]] = {
            int(team_id): [int(player_id) for player_id in player_ids]
            for team_id, player_ids in initial_state["team_player_map"].items()
        }
        score_map = {score.id: score for score in scores}
        team_points = {team_id: 0 for team_id in team_player_map}
        score_points: dict[int, int] = {}

        for round in rounds:
            round_start = datetime.fromisoformat(round["round_start"])
            cutoff_time = datetime.fromisoformat(round["cutoff_time"])

            if current_time < round_start:
                break

            eligible_players = {
                player_id
                for team_id in active_team_ids
                for player_id in team_player_map.get(team_id, [])
            }

            # gather scores
            for player_id in list(eligible_players):
                matching_score = next(
                    (
                        score
                        for score in scores
                        if score.player_id == player_id
                        and score.beatmap_id == round["beatmap_id"]
                        and round_start <= score.score_date <= cutoff_time
                    ),
                    None,
                )
                if matching_score is not None:
                    round["player_scores"][player_id] = matching_score.id
                    score_points[matching_score.id] = matching_score.score_score

            # aggregate team scores
            team_scores: dict[int, int] = {}
            for player_id, score_id in round["player_scores"].items():
                team_id = self._team_for_player(player_id, team_player_map)
                if team_id is not None:
                    score = score_map.get(score_id)
                    if score is not None:
                        team_scores[team_id] = (
                            team_scores.get(team_id, 0) + score.score_score
                        )
            round["team_scores"] = team_scores

            # process eliminations
            if current_time >= cutoff_time:
                ranked = sorted(
                    active_team_ids,
                    key=lambda team_id: (team_scores.get(team_id, -1), team_id),
                    reverse=True,
                )

                while len(ranked) > round["target_teams"]:
                    eliminated = ranked.pop()
                    active_team_ids.discard(eliminated)
                    round.setdefault("eliminated_team_ids", []).append(eliminated)

                for team_id in active_team_ids:
                    team_points[team_id] += 1

        player_points: dict[int, int] = {}
        for team_id, player_ids in team_player_map.items():
            for player_id in player_ids:
                player_points[player_id] = team_points[team_id]

        eliminated_team_ids = sorted(
            {
                team_id
                for round in rounds
                for team_id in round.get("eliminated_team_ids", [])
            }
        )

        return {
            "state": {
                "rounds": rounds,
                "active_team_ids": sorted(active_team_ids),
                "eliminated_team_ids": eliminated_team_ids,
                "team_player_map": team_player_map,
            },
            "win_condition_reached": len(active_team_ids) <= 1,
            "players": {
                player_id: {"points": points, "score_count": 0}
                for player_id, points in player_points.items()
            },
            "teams": {
                team_id: {"points": points, "score_count": 0}
                for team_id, points in team_points.items()
            },
            "scores": {
                score_id: {"points": points}
                for score_id, points in score_points.items()
            },
        }

    @staticmethod
    def _team_for_player(
        player_id: int, team_player_map: dict[int, list[int]]
    ) -> int | None:
        for team_id, player_ids in team_player_map.items():
            if player_id in player_ids:
                return team_id
        return None
