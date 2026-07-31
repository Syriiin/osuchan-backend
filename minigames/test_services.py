from datetime import datetime, timezone

import pytest

from common.osu.enums import BeatmapStatus, Gamemode
from minigames.enums import MinigameStatus
from minigames.models import Minigame, MinigamePlayer, MinigameScore, MinigameTeam
from minigames.services import update_minigame_player_scores
from profiles.enums import ScoreMutation, ScoreResult
from profiles.models import Beatmap, Score, UserStats


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
