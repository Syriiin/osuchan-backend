import json
import os
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import NamedTuple, Type

import requests
from django.conf import settings
from django.utils.module_loading import import_string
from ossapi import Beatmap, GameMode, Ossapi, Score, ScoreType, User, UserLookupKey

from common.osu.enums import BeatmapStatus, Gamemode
from common.osu.utils import get_bitwise_mods, get_json_mods


class MalformedResponseError(Exception):
    pass


class BeatmapData(NamedTuple):
    beatmap_id: int
    set_id: int
    gamemode: Gamemode
    status: BeatmapStatus

    artist: str
    title: str
    difficulty_name: str

    creator_name: str
    creator_id: int

    bpm: float
    max_combo: int | None
    drain_time: int
    total_time: int

    circle_size: float
    approach_rate: float
    overall_difficulty: float
    health_drain: float

    submission_date: datetime | None
    last_updated: datetime
    approval_date: datetime | None

    def as_json(self):
        return {
            "beatmap_id": self.beatmap_id,
            "set_id": self.set_id,
            "gamemode": self.gamemode.value,
            "status": self.status.value,
            "artist": self.artist,
            "title": self.title,
            "difficulty_name": self.difficulty_name,
            "creator_name": self.creator_name,
            "creator_id": self.creator_id,
            "bpm": self.bpm,
            "max_combo": self.max_combo,
            "drain_time": self.drain_time,
            "total_time": self.total_time,
            "circle_size": self.circle_size,
            "approach_rate": self.approach_rate,
            "overall_difficulty": self.overall_difficulty,
            "health_drain": self.health_drain,
            "submission_date": (
                self.submission_date.isoformat()
                if self.submission_date is not None
                else None
            ),
            "last_updated": self.last_updated.isoformat(),
            "approval_date": (
                self.approval_date.isoformat()
                if self.approval_date is not None
                else None
            ),
        }

    @classmethod
    def from_json(cls, data: dict) -> "BeatmapData":
        return cls(
            beatmap_id=data["beatmap_id"],
            set_id=data["set_id"],
            gamemode=Gamemode(data["gamemode"]),
            status=BeatmapStatus(data["status"]),
            artist=data["artist"],
            title=data["title"],
            difficulty_name=data["difficulty_name"],
            creator_name=data["creator_name"],
            creator_id=data["creator_id"],
            bpm=data["bpm"],
            max_combo=data["max_combo"],
            drain_time=data["drain_time"],
            total_time=data["total_time"],
            circle_size=data["circle_size"],
            approach_rate=data["approach_rate"],
            overall_difficulty=data["overall_difficulty"],
            health_drain=data["health_drain"],
            submission_date=(
                datetime.fromisoformat(data["submission_date"])
                if data["submission_date"] is not None
                else None
            ),
            last_updated=datetime.fromisoformat(data["last_updated"]),
            approval_date=(
                datetime.fromisoformat(data["approval_date"])
                if data["approval_date"] is not None
                else None
            ),
        )

    @classmethod
    def from_apiv1(cls, data: dict) -> "BeatmapData":
        return cls(
            beatmap_id=int(data["beatmap_id"]),
            set_id=int(data["beatmapset_id"]),
            gamemode=Gamemode(int(data["mode"])),
            status=BeatmapStatus(int(data["approved"])),
            artist=data["artist"],
            title=data["title"],
            difficulty_name=data["version"],
            creator_name=data["creator"],
            creator_id=int(data["creator_id"]),
            bpm=float(data["bpm"]),
            max_combo=int(data["max_combo"]) if data["max_combo"] != None else None,
            drain_time=int(data["hit_length"]),
            total_time=int(data["total_length"]),
            circle_size=float(data["diff_size"]),
            approach_rate=float(data["diff_approach"]),
            overall_difficulty=float(data["diff_overall"]),
            health_drain=float(data["diff_drain"]),
            submission_date=datetime.strptime(
                data["submit_date"], "%Y-%m-%d %H:%M:%S"
            ).replace(tzinfo=timezone.utc),
            last_updated=datetime.strptime(
                data["last_update"], "%Y-%m-%d %H:%M:%S"
            ).replace(tzinfo=timezone.utc),
            approval_date=(
                datetime.strptime(data["approved_date"], "%Y-%m-%d %H:%M:%S").replace(
                    tzinfo=timezone.utc
                )
                if data["approved_date"] != None
                else None
            ),
        )


class UserData(NamedTuple):
    user_id: int
    username: str
    join_date: datetime
    country: str
    playcount: int
    playtime: int
    level: float
    ranked_score: int
    total_score: int

    rank: int
    country_rank: int
    pp: float
    accuracy: float

    count_300: int
    count_100: int
    count_50: int

    count_rank_ss: int
    count_rank_ssh: int
    count_rank_s: int
    count_rank_sh: int
    count_rank_a: int

    def as_json(self):
        return {
            "user_id": self.user_id,
            "username": self.username,
            "join_date": self.join_date.isoformat(),
            "country": self.country,
            "playcount": self.playcount,
            "playtime": self.playtime,
            "level": self.level,
            "ranked_score": self.ranked_score,
            "total_score": self.total_score,
            "rank": self.rank,
            "country_rank": self.country_rank,
            "pp": self.pp,
            "accuracy": self.accuracy,
            "count_300": self.count_300,
            "count_100": self.count_100,
            "count_50": self.count_50,
            "count_rank_ss": self.count_rank_ss,
            "count_rank_ssh": self.count_rank_ssh,
            "count_rank_s": self.count_rank_s,
            "count_rank_sh": self.count_rank_sh,
            "count_rank_a": self.count_rank_a,
        }

    @classmethod
    def from_json(cls, data: dict) -> "UserData":
        return cls(
            user_id=data["user_id"],
            username=data["username"],
            join_date=datetime.fromisoformat(data["join_date"]),
            country=data["country"],
            playcount=data["playcount"],
            playtime=data["playtime"],
            level=data["level"],
            ranked_score=data["ranked_score"],
            total_score=data["total_score"],
            rank=data["rank"],
            country_rank=data["country_rank"],
            pp=data["pp"],
            accuracy=data["accuracy"],
            count_300=data["count_300"],
            count_100=data["count_100"],
            count_50=data["count_50"],
            count_rank_ss=data["count_rank_ss"],
            count_rank_ssh=data["count_rank_ssh"],
            count_rank_s=data["count_rank_s"],
            count_rank_sh=data["count_rank_sh"],
            count_rank_a=data["count_rank_a"],
        )

    @classmethod
    def from_apiv1(cls, data: dict) -> "UserData":
        return cls(
            user_id=int(data["user_id"]),
            username=data["username"],
            join_date=datetime.strptime(data["join_date"], "%Y-%m-%d %H:%M:%S").replace(
                tzinfo=timezone.utc
            ),
            country=data["country"],
            playcount=int(data["playcount"]) if data["playcount"] != None else 0,
            ranked_score=(
                int(data["ranked_score"]) if data["ranked_score"] != None else 0
            ),
            total_score=int(data["total_score"]) if data["total_score"] != None else 0,
            rank=int(data["pp_rank"]) if data["pp_rank"] != None else 0,
            country_rank=(
                int(data["pp_country_rank"]) if data["pp_country_rank"] != None else 0
            ),
            level=float(data["level"]) if data["level"] != None else 0,
            accuracy=float(data["accuracy"]) if data["accuracy"] != None else 0,
            count_rank_ss=(
                int(data["count_rank_ss"]) if data["count_rank_ss"] != None else 0
            ),
            count_rank_ssh=(
                int(data["count_rank_ssh"]) if data["count_rank_ssh"] != None else 0
            ),
            count_rank_s=(
                int(data["count_rank_s"]) if data["count_rank_s"] != None else 0
            ),
            count_rank_sh=(
                int(data["count_rank_sh"]) if data["count_rank_sh"] != None else 0
            ),
            count_rank_a=(
                int(data["count_rank_a"]) if data["count_rank_a"] != None else 0
            ),
            playtime=(
                int(data["total_seconds_played"])
                if data["total_seconds_played"] != None
                else 0
            ),
            pp=float(data["pp_raw"]) if data["pp_raw"] != None else 0,
            count_300=int(data["count300"]) if data["count300"] != None else 0,
            count_100=int(data["count100"]) if data["count100"] != None else 0,
            count_50=int(data["count50"]) if data["count50"] != None else 0,
        )


class ScoreData(NamedTuple):
    beatmap_id: int
    mods: int
    mods_json: list[dict]
    is_classic: bool

    score: int
    best_combo: int
    count_300: int
    count_100: int
    count_50: int
    count_miss: int
    count_katu: int
    count_geki: int
    statistics: dict[str, int]

    perfect: bool
    rank: str
    date: datetime

    def as_json(self):
        return {
            "beatmap_id": self.beatmap_id,
            "mods": self.mods,
            "mods_json": self.mods_json,
            "is_classic": self.is_classic,
            "score": self.score,
            "best_combo": self.best_combo,
            "count_300": self.count_300,
            "count_100": self.count_100,
            "count_50": self.count_50,
            "count_miss": self.count_miss,
            "count_katu": self.count_katu,
            "count_geki": self.count_geki,
            "statistics": self.statistics,
            "perfect": self.perfect,
            "rank": self.rank,
            "date": self.date.isoformat(),
        }

    @classmethod
    def from_json(cls, data: dict) -> "ScoreData":
        return cls(
            beatmap_id=data["beatmap_id"],
            mods=data["mods"],
            mods_json=data["mods_json"],
            is_classic=data["is_classic"],
            score=data["score"],
            best_combo=data["best_combo"],
            count_300=data["count_300"],
            count_100=data["count_100"],
            count_50=data["count_50"],
            count_miss=data["count_miss"],
            count_katu=data["count_katu"],
            count_geki=data["count_geki"],
            statistics=data["statistics"],
            perfect=data["perfect"],
            rank=data["rank"],
            date=datetime.fromisoformat(data["date"]),
        )

    @classmethod
    def from_apiv1(
        cls, data: dict, gamemode: Gamemode, beatmap_id_override: int | None = None
    ) -> "ScoreData":
        statistics = {}

        if gamemode == Gamemode.STANDARD:
            if data["count300"] != "0":
                statistics["great"] = int(data["count300"])
            if data["count100"] != "0":
                statistics["ok"] = int(data["count100"])
            if data["count50"] != "0":
                statistics["meh"] = int(data["count50"])
            if data["countmiss"] != "0":
                statistics["miss"] = int(data["countmiss"])
        elif gamemode == Gamemode.TAIKO:
            if data["count300"] != "0":
                statistics["great"] = int(data["count300"])
            if data["count100"] != "0":
                statistics["ok"] = int(data["count100"])
            if data["countmiss"] != "0":
                statistics["miss"] = int(data["countmiss"])
        elif gamemode == Gamemode.CATCH:
            if data["count300"] != "0":
                statistics["great"] = int(data["count300"])
            if data["countmiss"] != "0":
                statistics["miss"] = int(data["countmiss"])
            if data["count100"] != "0":
                statistics["large_tick_hit"] = int(data["count100"])
            if data["count50"] != "0":
                statistics["small_tick_hit"] = int(data["count50"])
            if data["countkatu"] != "0":
                statistics["small_tick_miss"] = int(data["countkatu"])
        elif gamemode == Gamemode.MANIA:
            if data["countgeki"] != "0":
                statistics["perfect"] = int(data["countgeki"])
            if data["count300"] != "0":
                statistics["great"] = int(data["count300"])
            if data["countkatu"] != "0":
                statistics["good"] = int(data["countkatu"])
            if data["count100"] != "0":
                statistics["ok"] = int(data["count100"])
            if data["count50"] != "0":
                statistics["meh"] = int(data["count50"])
            if data["countmiss"] != "0":
                statistics["miss"] = int(data["countmiss"])

        is_classic = data["score"] != "0"  # lazer uses new scoring

        return cls(
            beatmap_id=(
                beatmap_id_override
                if beatmap_id_override is not None
                else int(data["beatmap_id"])
            ),
            mods=int(data["enabled_mods"]),
            mods_json=get_json_mods(int(data["enabled_mods"]), is_classic),
            is_classic=is_classic,
            score=int(data["score"]),
            best_combo=int(data["maxcombo"]),
            count_300=int(data["count300"]),
            count_100=int(data["count100"]),
            count_50=int(data["count50"]),
            count_miss=int(data["countmiss"]),
            count_katu=int(data["countkatu"]),
            count_geki=int(data["countgeki"]),
            statistics=statistics,
            perfect=bool(int(data["perfect"])),
            rank=data["rank"],
            date=datetime.strptime(data["date"], "%Y-%m-%d %H:%M:%S").replace(
                tzinfo=timezone.utc
            ),
        )


class AbstractOsuApi(ABC):
    @abstractmethod
    def get_beatmap(self, beatmap_id: int) -> BeatmapData | None:
        raise NotImplementedError()

    @abstractmethod
    def get_user_by_id(self, user_id: int, gamemode: Gamemode) -> UserData | None:
        raise NotImplementedError()

    @abstractmethod
    def get_user_by_name(self, username: str, gamemode: Gamemode) -> UserData | None:
        raise NotImplementedError()

    @abstractmethod
    def get_user_scores_for_beatmap(
        self, beatmap_id: int, user_id: int, gamemode: Gamemode
    ) -> list[ScoreData]:
        raise NotImplementedError()

    @abstractmethod
    def get_user_best_scores(self, user_id: int, gamemode: Gamemode) -> list[ScoreData]:
        raise NotImplementedError()

    @abstractmethod
    def get_user_recent_scores(
        self, user_id: int, gamemode: Gamemode
    ) -> list[ScoreData]:
        raise NotImplementedError()


class LiveOsuApiV1(AbstractOsuApi):
    def __get_legacy_endpoint(self, endpoint_name, **kwargs) -> list[dict]:
        # Remove any None arguments passed in kwargs
        payload = {k: v for k, v in kwargs.items() if v is not None}

        # Add api key to payload
        payload["k"] = settings.OSU_API_V1_KEY

        # Return result of GET request
        response = requests.get(
            settings.OSU_API_V1_BASE_URL + endpoint_name, params=payload
        )
        response.raise_for_status()

        return response.json()

    def get_beatmap(self, beatmap_id: int) -> BeatmapData | None:
        try:
            return BeatmapData.from_apiv1(
                self.__get_legacy_endpoint("get_beatmaps", b=beatmap_id)[0]
            )
        except IndexError:
            return None

    def get_user_by_id(self, user_id: int, gamemode: Gamemode) -> UserData | None:
        try:
            return UserData.from_apiv1(
                self.__get_legacy_endpoint(
                    "get_user", u=user_id, type="id", m=gamemode.value
                )[0]
            )
        except IndexError:
            return None

    def get_user_by_name(self, username: str, gamemode: Gamemode) -> UserData | None:
        try:
            return UserData.from_apiv1(
                self.__get_legacy_endpoint(
                    "get_user", u=username, type="string", m=gamemode.value
                )[0]
            )
        except IndexError:
            return None

    def get_user_scores_for_beatmap(
        self, beatmap_id: int, user_id: int, gamemode: Gamemode
    ) -> list[ScoreData]:
        return [
            ScoreData.from_apiv1(data, gamemode, beatmap_id)
            for data in self.__get_legacy_endpoint(
                "get_scores", b=beatmap_id, u=user_id, type="id", m=gamemode.value
            )
        ]

    def get_user_best_scores(self, user_id: int, gamemode: Gamemode) -> list[ScoreData]:
        return [
            ScoreData.from_apiv1(data, gamemode)
            for data in self.__get_legacy_endpoint(
                "get_user_best", u=user_id, type="id", m=gamemode.value, limit=100
            )
        ]

    def get_user_recent_scores(
        self, user_id: int, gamemode: Gamemode
    ) -> list[ScoreData]:
        return [
            ScoreData.from_apiv1(data, gamemode)
            for data in self.__get_legacy_endpoint(
                "get_user_recent", u=user_id, type="id", m=gamemode.value, limit=50
            )
        ]


class LiveOsuApiV2(AbstractOsuApi):
    def __init__(self):
        self.client = Ossapi(
            settings.OSU_CLIENT_ID,
            settings.OSU_CLIENT_SECRET,
            token_directory="/tmp",
        )

    @staticmethod
    def __get_ossapi_gamemode(gamemode: Gamemode) -> GameMode:
        return {
            Gamemode.STANDARD: GameMode.OSU,
            Gamemode.TAIKO: GameMode.TAIKO,
            Gamemode.CATCH: GameMode.CATCH,
            Gamemode.MANIA: GameMode.MANIA,
        }[gamemode]

    @staticmethod
    def __beatmap_data_from_ossapi(beatmap: Beatmap) -> BeatmapData:
        beatmap_set = beatmap.beatmapset()
        return BeatmapData(
            beatmap_id=beatmap.id,
            set_id=beatmap.beatmapset_id,
            gamemode=Gamemode(beatmap.mode_int),
            status=BeatmapStatus(beatmap.status.value),
            artist=beatmap_set.artist,
            title=beatmap_set.title,
            difficulty_name=beatmap.version,
            creator_name=beatmap_set.creator,
            creator_id=beatmap_set.user_id,
            bpm=beatmap.bpm or beatmap_set.bpm,  # TODO: investigate why nullable
            max_combo=beatmap.max_combo,
            drain_time=beatmap.hit_length,
            total_time=beatmap.total_length,
            circle_size=beatmap.cs,
            approach_rate=beatmap.ar,
            overall_difficulty=beatmap.accuracy,
            health_drain=beatmap.drain,
            submission_date=beatmap_set.submitted_date,
            last_updated=beatmap_set.last_updated,
            approval_date=beatmap_set.ranked_date,
        )

    @staticmethod
    def __user_data_from_ossapi(user: User) -> UserData:
        stats = user.statistics
        grade_counts = stats.grade_counts if stats is not None else None
        return UserData(
            user_id=user.id,
            username=user.username,
            join_date=user.join_date,
            country=user.country_code,
            playcount=stats.play_count if stats is not None else 0,
            playtime=stats.play_time if stats is not None else 0,
            level=(
                stats.level.current + stats.level.progress / 100
                if stats is not None
                else 0
            ),
            ranked_score=stats.ranked_score if stats is not None else 0,
            total_score=stats.total_score if stats is not None else 0,
            rank=stats.global_rank or 0 if stats is not None else 0,
            country_rank=stats.country_rank or 0 if stats is not None else 0,
            pp=stats.pp if stats is not None else 0,
            accuracy=stats.hit_accuracy if stats is not None else 0,
            count_300=stats.count_300 if stats is not None else 0,
            count_100=stats.count_100 if stats is not None else 0,
            count_50=stats.count_50 if stats is not None else 0,
            count_rank_ss=grade_counts.ss if grade_counts is not None else 0,
            count_rank_ssh=grade_counts.ssh if grade_counts is not None else 0,
            count_rank_s=grade_counts.s if grade_counts is not None else 0,
            count_rank_sh=grade_counts.sh if grade_counts is not None else 0,
            count_rank_a=grade_counts.a if grade_counts is not None else 0,
        )

    @staticmethod
    def __score_data_from_ossapi(
        score: Score, gamemode: Gamemode, beatmap_id_override: int | None = None
    ) -> ScoreData:
        if beatmap_id_override is None:
            if score.beatmap is None:
                raise MalformedResponseError("Score does not have a beatmap")
            else:
                beatmap_id = score.beatmap.id
        else:
            beatmap_id = beatmap_id_override

        bitwise_mods, is_classic = get_bitwise_mods([mod.acronym for mod in score.mods])

        mods_json = []
        for mod in score.mods:
            mod_json = {"acronym": mod.acronym}
            if mod.settings is not None:
                mod_json["settings"] = mod.settings
            mods_json.append(mod_json)

        if gamemode == Gamemode.STANDARD:
            count_300 = (
                score.statistics.great if score.statistics.great is not None else 0
            )
            count_100 = score.statistics.ok if score.statistics.ok is not None else 0
            count_50 = score.statistics.meh if score.statistics.meh is not None else 0
            count_miss = (
                score.statistics.miss if score.statistics.miss is not None else 0
            )
            count_katu = 0
            count_geki = 0
        elif gamemode == Gamemode.TAIKO:
            count_300 = (
                score.statistics.great if score.statistics.great is not None else 0
            )
            count_100 = score.statistics.ok if score.statistics.ok is not None else 0
            count_50 = 0
            count_miss = (
                score.statistics.miss if score.statistics.miss is not None else 0
            )
            count_katu = 0
            count_geki = (
                score.statistics.large_bonus
                if score.statistics.large_bonus is not None
                else 0
            )
        elif gamemode == Gamemode.CATCH:
            count_300 = (
                score.statistics.great if score.statistics.great is not None else 0
            )
            count_100 = (
                score.statistics.large_tick_hit
                if score.statistics.large_tick_hit is not None
                else 0
            )
            count_50 = (
                score.statistics.small_tick_hit
                if score.statistics.small_tick_hit is not None
                else 0
            )
            count_miss = (
                score.statistics.miss if score.statistics.miss is not None else 0
            )
            count_katu = (
                score.statistics.small_tick_miss
                if score.statistics.small_tick_miss is not None
                else 0
            )
            count_geki = 0
        elif gamemode == Gamemode.MANIA:
            count_300 = (
                score.statistics.great if score.statistics.great is not None else 0
            )
            count_100 = score.statistics.ok if score.statistics.ok is not None else 0
            count_50 = score.statistics.meh if score.statistics.meh is not None else 0
            count_miss = (
                score.statistics.miss if score.statistics.miss is not None else 0
            )
            count_katu = (
                score.statistics.good if score.statistics.good is not None else 0
            )
            count_geki = (
                score.statistics.perfect if score.statistics.perfect is not None else 0
            )
        else:
            raise ValueError(f"{gamemode} is not a valid gamemode")

        statistics = {}

        if score.statistics.miss is not None:
            statistics["miss"] = score.statistics.miss
        if score.statistics.meh is not None:
            statistics["meh"] = score.statistics.meh
        if score.statistics.ok is not None:
            statistics["ok"] = score.statistics.ok
        if score.statistics.good is not None:
            statistics["good"] = score.statistics.good
        if score.statistics.great is not None:
            statistics["great"] = score.statistics.great
        if score.statistics.perfect is not None:
            statistics["perfect"] = score.statistics.perfect
        if score.statistics.small_tick_miss is not None:
            statistics["small_tick_miss"] = score.statistics.small_tick_miss
        if score.statistics.small_tick_hit is not None:
            statistics["small_tick_hit"] = score.statistics.small_tick_hit
        if score.statistics.large_tick_miss is not None:
            statistics["large_tick_miss"] = score.statistics.large_tick_miss
        if score.statistics.large_tick_hit is not None:
            statistics["large_tick_hit"] = score.statistics.large_tick_hit
        if score.statistics.small_bonus is not None:
            statistics["small_bonus"] = score.statistics.small_bonus
        if score.statistics.large_bonus is not None:
            statistics["large_bonus"] = score.statistics.large_bonus
        if score.statistics.ignore_miss is not None:
            statistics["ignore_miss"] = score.statistics.ignore_miss
        if score.statistics.ignore_hit is not None:
            statistics["ignore_hit"] = score.statistics.ignore_hit
        if score.statistics.combo_break is not None:
            statistics["combo_break"] = score.statistics.combo_break
        if score.statistics.slider_tail_hit is not None:
            statistics["slider_tail_hit"] = score.statistics.slider_tail_hit
        if score.statistics.legacy_combo_increase is not None:
            statistics["legacy_combo_increase"] = score.statistics.legacy_combo_increase

        return ScoreData(
            beatmap_id=beatmap_id,
            mods=bitwise_mods,
            mods_json=mods_json,
            is_classic=is_classic,
            score=score.legacy_total_score if is_classic else score.total_score,
            best_combo=score.max_combo,
            count_300=count_300,
            count_100=count_100,
            count_50=count_50,
            count_miss=count_miss,
            count_katu=count_katu,
            count_geki=count_geki,
            statistics=statistics,
            perfect=score.legacy_perfect,
            rank=score.rank.value,
            date=score.ended_at,  # pretty sure this is a typing bug. should be non-nullable
        )

    def get_beatmap(self, beatmap_id: int) -> BeatmapData | None:
        try:
            beatmap = self.client.beatmap(beatmap_id)
        except ValueError:
            return None

        return self.__beatmap_data_from_ossapi(beatmap)

    def get_user_by_id(self, user_id: int, gamemode: Gamemode) -> UserData | None:
        try:
            user = self.client.user(
                user_id, mode=self.__get_ossapi_gamemode(gamemode), key=UserLookupKey.ID
            )
        except ValueError:
            return None

        return self.__user_data_from_ossapi(user)

    def get_user_by_name(self, username: str, gamemode: Gamemode) -> UserData | None:
        try:
            user = self.client.user(
                username,
                mode=self.__get_ossapi_gamemode(gamemode),
                key=UserLookupKey.USERNAME,
            )
        except ValueError:
            return None

        return self.__user_data_from_ossapi(user)

    def get_user_scores_for_beatmap(
        self, beatmap_id: int, user_id: int, gamemode: Gamemode
    ) -> list[ScoreData]:
        try:
            scores = self.client.beatmap_user_scores(
                beatmap_id,
                user_id,
                mode=self.__get_ossapi_gamemode(gamemode),
            )
        except ValueError:
            return []

        return [
            self.__score_data_from_ossapi(score, gamemode, beatmap_id)
            for score in scores
        ]

    def get_user_best_scores(self, user_id: int, gamemode: Gamemode) -> list[ScoreData]:
        try:
            scores = self.client.user_scores(
                user_id,
                ScoreType.BEST,
                mode=self.__get_ossapi_gamemode(gamemode),
                limit=100,
            )
        except ValueError:
            return []

        return [self.__score_data_from_ossapi(score, gamemode) for score in scores]

    def get_user_recent_scores(
        self, user_id: int, gamemode: Gamemode
    ) -> list[ScoreData]:
        try:
            scores = self.client.user_scores(
                user_id,
                ScoreType.RECENT,
                mode=self.__get_ossapi_gamemode(gamemode),
                limit=50,
            )
        except ValueError:
            return []

        return [self.__score_data_from_ossapi(score, gamemode) for score in scores]


class StubOsuApi(AbstractOsuApi):
    def __load_stub_data__(self, filename: str) -> dict:
        with open(
            os.path.join(os.path.dirname(__file__), "stubdata", "osuapi", filename)
        ) as fp:
            return json.load(fp)

    def get_beatmap(self, beatmap_id: int) -> BeatmapData | None:
        try:
            return BeatmapData.from_json(
                self.__load_stub_data__("beatmaps.json")[str(beatmap_id)]
            )
        except KeyError:
            return None

    def get_user_by_id(self, user_id: int, gamemode: Gamemode) -> UserData | None:
        try:
            return UserData.from_json(
                self.__load_stub_data__("users.json")[str(user_id)][str(gamemode.value)]
            )
        except KeyError:
            return None

    def get_user_by_name(self, username: str, gamemode: Gamemode) -> UserData | None:
        users = self.__load_stub_data__("users.json")

        gamemode_str = str(gamemode.value)

        try:
            return next(
                UserData.from_json(users[user][gamemode_str])
                for user in users
                if users[user][gamemode_str]["username"].lower() == username.lower()
            )
        except (KeyError, StopIteration):
            return None

    def get_user_scores_for_beatmap(
        self, beatmap_id: int, user_id: int, gamemode: Gamemode
    ) -> list[ScoreData]:
        try:
            return [
                ScoreData.from_json(data)
                for data in self.__load_stub_data__("scores.json")[str(user_id)][
                    str(gamemode.value)
                ][str(beatmap_id)]
            ]
        except KeyError:
            return []

    def get_user_best_scores(self, user_id: int, gamemode: Gamemode) -> list[ScoreData]:
        try:
            return [
                ScoreData.from_json(data)
                for data in self.__load_stub_data__("user_best.json")[str(user_id)][
                    str(gamemode.value)
                ]
            ]
        except KeyError:
            return []

    def get_user_recent_scores(
        self, user_id: int, gamemode: Gamemode
    ) -> list[ScoreData]:
        try:
            return [
                ScoreData.from_json(data)
                for data in self.__load_stub_data__("user_recent.json")[str(user_id)][
                    str(gamemode.value)
                ]
            ]
        except KeyError:
            return []


OsuApi: Type[AbstractOsuApi] = import_string(settings.OSU_API_CLASS)
