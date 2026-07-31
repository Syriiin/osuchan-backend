from datetime import datetime, timezone

import pytest

from common.osu.enums import BeatmapStatus, Gamemode
from minigames.enums import MinigameStatus
from minigames.games.base import MinigameConfigError
from minigames.models import Minigame, MinigamePlayer, MinigameScore, MinigameStats, MinigameTeam
from minigames.services import (
    create_minigame,
    finish_minigame,
    recompute_minigame,
    start_minigame,
    update_minigame_player_scores,
    update_minigame_settings,
)
from profiles.enums import ScoreMutation, ScoreResult
from profiles.models import Beatmap, OsuUser, Score, UserStats


@pytest.fixture
def minigame(osu_user):
    return Minigame.objects.create(
        game_type="battle_royale",
        name="test minigame",
        gamemode=Gamemode.STANDARD,
        status=MinigameStatus.IN_PROGRESS,
        start_time=datetime(2023, 1, 1, tzinfo=timezone.utc),
        end_time=datetime(2024, 1, 1, tzinfo=timezone.utc),
        config={},
        initial_state={},
        state={},
        is_free_for_all=False,
        host=osu_user,
    )


@pytest.fixture
def minigame_team(minigame):
    return MinigameTeam.objects.create(
        name="team", points=0, score_count=0, minigame=minigame
    )


@pytest.fixture
def minigame_player(minigame_team, osu_user):
    return MinigamePlayer.objects.create(
        team=minigame_team, user=osu_user, points=0, score_count=0
    )


@pytest.fixture
def loved_beatmap():
    return Beatmap.objects.create(
        id=100,
        set_id=10,
        artist="test artist",
        title="loved map",
        difficulty_name="test difficulty",
        gamemode=Gamemode.STANDARD,
        status=BeatmapStatus.LOVED,
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
    )


def _score(user_stats: UserStats, beatmap: Beatmap):
    return Score.objects.create(
        score=1000000,
        count_300=1739,
        count_100=0,
        count_50=0,
        count_miss=0,
        count_geki=360,
        count_katu=0,
        statistics={"great": 1739, "ok": 0, "meh": 0, "miss": 0},
        best_combo=2843,
        perfect=True,
        mods=0,
        mods_json={},
        is_stable=True,
        rank="X",
        date=datetime(2023, 6, 1, tzinfo=timezone.utc),
        beatmap=beatmap,
        user_stats=user_stats,
        gamemode=Gamemode.STANDARD,
        accuracy=100.0,
        bpm=180,
        length=120,
        circle_size=4,
        approach_rate=8,
        overall_difficulty=6,
        result=ScoreResult.PERFECT,
        mutation=ScoreMutation.NONE,
    )


@pytest.mark.django_db
class TestUpdateMinigamePlayerScores:
    def test_loved_map_score_included(self, user_stats, minigame_player, loved_beatmap):
        score = _score(user_stats, loved_beatmap)

        update_minigame_player_scores(minigame_player)

        assert MinigameScore.objects.filter(score=score).exists()

    def test_pending_map_score_excluded(
        self, user_stats, minigame_player, loved_beatmap
    ):
        loved_beatmap.status = BeatmapStatus.PENDING
        loved_beatmap.save(update_fields=["status"])
        score = _score(user_stats, loved_beatmap)

        update_minigame_player_scores(minigame_player)

        assert not MinigameScore.objects.filter(score=score).exists()


@pytest.fixture
def lobby_minigame(osu_user):
    second_user = OsuUser.objects.create(
        id=2,
        username="SecondOsuUser",
        country="au",
        join_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
        disabled=False,
    )
    minigame = Minigame.objects.create(
        game_type="battle_royale",
        name="test minigame",
        gamemode=Gamemode.STANDARD,
        status=MinigameStatus.LOBBY,
        config={
            "beatmaps": [],
            "elimination_mode": "auto",
            "game_length": 3600,
            "play_start_window": 30,
            "submission_buffer": 30,
            "intermission": 60,
        },
        initial_state={},
        state={},
        is_free_for_all=False,
        host=osu_user,
    )
    team_a = MinigameTeam.objects.create(
        name="A", points=0, score_count=0, minigame=minigame
    )
    team_b = MinigameTeam.objects.create(
        name="B", points=0, score_count=0, minigame=minigame
    )
    MinigamePlayer.objects.create(
        team=team_a, user=osu_user, points=0, score_count=0
    )
    MinigamePlayer.objects.create(
        team=team_b, user=second_user, points=0, score_count=0
    )
    return minigame


@pytest.mark.django_db
class TestRecomputeMinigame:
    def test_json_round_tripped_team_ids(self, lobby_minigame):
        minigame = start_minigame(lobby_minigame, countdown=0)
        minigame.refresh_from_db()
        assert minigame.status == MinigameStatus.WAITING_TO_START

        win_reached = recompute_minigame(minigame)

        assert win_reached is False
        teams = list(minigame.teams.all())
        assert len(teams) == 2
        assert all(team.points == 0 for team in teams)


@pytest.mark.django_db
class TestFinishMinigame:
    def test_already_finished_minigame_does_not_double_count_wins(self, lobby_minigame):
        minigame = lobby_minigame
        minigame.status = MinigameStatus.FINALISING
        winning_team = minigame.teams.get(name="A")
        minigame.winning_team = winning_team
        minigame.save()

        winning_player = winning_team.players.get()
        stats = MinigameStats.objects.create(user=winning_player.user, wins=1)

        minigame = finish_minigame(minigame)

        assert minigame.status == MinigameStatus.FINISHED
        assert minigame.winning_team == winning_team
        stats.refresh_from_db()
        assert stats.wins == 1

    def test_finish_minigame_tie_declares_no_winner(self, lobby_minigame):
        minigame = start_minigame(lobby_minigame, countdown=0)
        minigame.refresh_from_db()
        minigame.status = MinigameStatus.FINALISING
        minigame.save(update_fields=["status"])

        minigame = finish_minigame(minigame)

        assert minigame.status == MinigameStatus.FINISHED
        assert minigame.winning_team is None


@pytest.mark.django_db
class TestCreateMinigame:
    def test_battle_royale_requires_beatmaps(self, osu_user):
        with pytest.raises(MinigameConfigError):
            create_minigame(
                game_type="battle_royale",
                name="test minigame",
                gamemode=Gamemode.STANDARD,
                host=osu_user,
                settings_data={},
                teams=["A", "B"],
            )

    def test_battle_royale_unknown_beatmap_raises(self, osu_user):
        with pytest.raises(MinigameConfigError):
            create_minigame(
                game_type="battle_royale",
                name="test minigame",
                gamemode=Gamemode.STANDARD,
                host=osu_user,
                settings_data={"beatmaps": [{"beatmap_id": 999}]},
                teams=["A", "B"],
            )

    def test_lockout_bingo_does_not_require_beatmaps(self, osu_user):
        minigame = create_minigame(
            game_type="lockout_bingo",
            name="test minigame",
            gamemode=Gamemode.STANDARD,
            host=osu_user,
            settings_data={},
            teams=["A", "B"],
        )
        assert minigame.game_type == "lockout_bingo"
        assert minigame.status == MinigameStatus.LOBBY


@pytest.mark.django_db
class TestUpdateMinigameSettings:
    def test_battle_royale_rejects_empty_beatmaps(self, lobby_minigame):
        with pytest.raises(MinigameConfigError):
            update_minigame_settings(lobby_minigame, {"beatmaps": []})
