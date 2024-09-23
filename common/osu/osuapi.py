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

    score: int
    best_combo: int
    count_300: int
    count_100: int
    count_50: int
    count_miss: int
    count_katu: int
    count_geki: int

    perfect: bool
    rank: str
    date: datetime

    @classmethod
    def from_apiv1(
        cls, data: dict, beatmap_id_override: int | None = None
    ) -> "ScoreData":
        return cls(
            beatmap_id=(
                beatmap_id_override
                if beatmap_id_override is not None
                else int(data["beatmap_id"])
            ),
            mods=int(data["enabled_mods"]),
            score=int(data["score"]),
            best_combo=int(data["maxcombo"]),
            count_300=int(data["count300"]),
            count_100=int(data["count100"]),
            count_50=int(data["count50"]),
            count_miss=int(data["countmiss"]),
            count_katu=int(data["countkatu"]),
            count_geki=int(data["countgeki"]),
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
            ScoreData.from_apiv1(data, beatmap_id)
            for data in self.__get_legacy_endpoint(
                "get_scores", b=beatmap_id, u=user_id, type="id", m=gamemode.value
            )
        ]

    def get_user_best_scores(self, user_id: int, gamemode: Gamemode) -> list[ScoreData]:
        return [
            ScoreData.from_apiv1(data)
            for data in self.__get_legacy_endpoint(
                "get_user_best", u=user_id, type="id", m=gamemode.value, limit=100
            )
        ]

    def get_user_recent_scores(
        self, user_id: int, gamemode: Gamemode
    ) -> list[ScoreData]:
        return [
            ScoreData.from_apiv1(data)
            for data in self.__get_legacy_endpoint(
                "get_user_recent", u=user_id, type="id", m=gamemode.value, limit=50
            )
        ]


class StubOsuApiV1(AbstractOsuApi):
    def __load_stub_data__(self, filename: str) -> dict:
        with open(
            os.path.join(os.path.dirname(__file__), "stubdata", "osuapi", filename)
        ) as fp:
            return json.load(fp)

    def get_beatmap(self, beatmap_id: int) -> BeatmapData | None:
        try:
            return BeatmapData.from_apiv1(
                self.__load_stub_data__("beatmaps.json")[str(beatmap_id)]
            )
        except KeyError:
            return None

    def get_user_by_id(self, user_id: int, gamemode: Gamemode) -> UserData | None:
        try:
            return UserData.from_apiv1(
                self.__load_stub_data__("users.json")[str(user_id)][str(gamemode.value)]
            )
        except KeyError:
            return None

    def get_user_by_name(self, username: str, gamemode: Gamemode) -> UserData | None:
        users = self.__load_stub_data__("users.json")

        gamemode_str = str(gamemode.value)

        try:
            return next(
                UserData.from_apiv1(users[user][gamemode_str])
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
                ScoreData.from_apiv1(data, beatmap_id)
                for data in self.__load_stub_data__("scores.json")[str(user_id)][
                    str(gamemode.value)
                ][str(beatmap_id)]
            ]
        except KeyError:
            return []

    def get_user_best_scores(self, user_id: int, gamemode: Gamemode) -> list[ScoreData]:
        try:
            return [
                ScoreData.from_apiv1(data)
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
                ScoreData.from_apiv1(data)
                for data in self.__load_stub_data__("user_recent.json")[str(user_id)][
                    str(gamemode.value)
                ]
            ]
        except KeyError:
            return []


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
        score: Score, beatmap_id_override: int | None = None
    ) -> ScoreData:
        if beatmap_id_override is None:
            if score.beatmap is None:
                raise MalformedResponseError("Score does not have a beatmap")
            else:
                beatmap_id = score.beatmap.id
        else:
            beatmap_id = beatmap_id_override

        return ScoreData(
            beatmap_id=beatmap_id,
            mods=score.mods.value,
            score=score.score,
            best_combo=score.max_combo,
            count_300=(
                score.statistics.count_300
                if score.statistics.count_300 is not None
                else 0
            ),
            count_100=(
                score.statistics.count_100
                if score.statistics.count_100 is not None
                else 0
            ),
            count_50=(
                score.statistics.count_50
                if score.statistics.count_50 is not None
                else 0
            ),
            count_miss=(
                score.statistics.count_miss
                if score.statistics.count_miss is not None
                else 0
            ),
            count_katu=(
                score.statistics.count_katu
                if score.statistics.count_katu is not None
                else 0
            ),
            count_geki=(
                score.statistics.count_geki
                if score.statistics.count_geki is not None
                else 0
            ),
            perfect=score.perfect,
            rank=score.rank.value,
            date=score.created_at,
        )

    def get_beatmap(self, beatmap_id: int) -> BeatmapData | None:
        beatmap = self.client.beatmap(beatmap_id)
        return self.__beatmap_data_from_ossapi(beatmap)

    def get_user_by_id(self, user_id: int, gamemode: Gamemode) -> UserData | None:
        user = self.client.user(
            user_id, mode=self.__get_ossapi_gamemode(gamemode), key=UserLookupKey.ID
        )
        return self.__user_data_from_ossapi(user)

    def get_user_by_name(self, username: str, gamemode: Gamemode) -> UserData | None:
        user = self.client.user(
            username,
            mode=self.__get_ossapi_gamemode(gamemode),
            key=UserLookupKey.USERNAME,
        )
        return self.__user_data_from_ossapi(user)

    def get_user_scores_for_beatmap(
        self, beatmap_id: int, user_id: int, gamemode: Gamemode
    ) -> list[ScoreData]:
        scores = self.client.beatmap_user_scores(
            beatmap_id,
            user_id,
            mode=self.__get_ossapi_gamemode(gamemode),
        )
        return [self.__score_data_from_ossapi(score, beatmap_id) for score in scores]

    def get_user_best_scores(self, user_id: int, gamemode: Gamemode) -> list[ScoreData]:
        scores = self.client.user_scores(
            user_id,
            ScoreType.BEST,
            mode=self.__get_ossapi_gamemode(gamemode),
            limit=100,
        )
        return [self.__score_data_from_ossapi(score) for score in scores]

    def get_user_recent_scores(
        self, user_id: int, gamemode: Gamemode
    ) -> list[ScoreData]:
        scores = self.client.user_scores(
            user_id,
            ScoreType.RECENT,
            mode=self.__get_ossapi_gamemode(gamemode),
            limit=50,
        )
        return [self.__score_data_from_ossapi(score) for score in scores]


OsuApi: Type[AbstractOsuApi] = import_string(settings.OSU_API_CLASS)
