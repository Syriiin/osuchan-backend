from datetime import datetime, timezone

import pytest

from common.osu.enums import Gamemode, Mods
from osuauth.models import User
from profiles.enums import ScoreResult
from profiles.models import Beatmap, OsuUser, Score, ScoreFilter, UserStats


@pytest.fixture
def user():
    return User.objects.create(username="testusername")


@pytest.fixture
def osu_user():
    return OsuUser.objects.create(
        id=1,
        username="TestOsuUser",
        country="au",
        join_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
        disabled=False,
    )


@pytest.fixture
def user_stats(osu_user: OsuUser):
    return UserStats.objects.create(
        gamemode=Gamemode.STANDARD,
        playcount=52382,
        playtime=3431127,
        level=100.123,
        ranked_score=12389457398,
        total_score=94838472933,
        rank=52384,
        country_rank=2382,
        pp=5238.23,
        accuracy=97.35725931489383,
        count_300=11698772,
        count_100=1223376,
        count_50=97413,
        count_rank_ss=25,
        count_rank_ssh=15,
        count_rank_s=254,
        count_rank_sh=424,
        count_rank_a=908,
        extra_pp=0,
        score_style_accuracy=0,
        score_style_bpm=0,
        score_style_cs=0,
        score_style_ar=0,
        score_style_od=0,
        score_style_length=0,
        user=osu_user,
    )


@pytest.fixture
def beatmap():
    return Beatmap.objects.create(
        id=1,
        set_id=1,
        artist="test artist",
        title="test title",
        difficulty_name="test difficulty",
        gamemode=Gamemode.STANDARD,
        status=1,
        creator_name="test creator",
        bpm=180,
        drain_time=556,
        total_time=682,
        max_combo=2843,
        circle_size=4,
        overall_difficulty=6,
        approach_rate=8,
        health_drain=5,
        submission_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
        approval_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
        last_updated=datetime(2023, 1, 1, tzinfo=timezone.utc),
        difficulty_total=4.4574,
        difficulty_calculator_engine="test diffcalc engine",
        difficulty_calculator_version="test diffcalc version",
        creator_id=1,
    )


@pytest.fixture
def score(user_stats: UserStats, beatmap: Beatmap):
    return Score.objects.create(
        score=137805806,
        count_300=1739,
        count_100=14,
        count_50=0,
        count_miss=0,
        count_geki=360,
        count_katu=7,
        best_combo=2757,
        perfect=False,
        mods=Mods.DOUBLETIME + Mods.HIDDEN + Mods.SUDDEN_DEATH,
        rank="SH",
        date=datetime(2023, 1, 1, tzinfo=timezone.utc),
        beatmap=beatmap,
        user_stats=user_stats,
        gamemode=Gamemode.STANDARD,
        accuracy=99.47,
        bpm=182,
        length=368,
        circle_size=4,
        approach_rate=9.7,
        overall_difficulty=8.4,
        performance_total=395.282,
        nochoke_performance_total=395.282,
        difficulty_total=6.26,
        difficulty_calculator_engine="test diffcalc engine",
        difficulty_calculator_version="test diffcalc version",
        result=ScoreResult.NO_BREAK,
    )


@pytest.fixture
def score_filter():
    return ScoreFilter.objects.create(required_mods=Mods.HIDDEN)
