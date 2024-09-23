import json
import os
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import NamedTuple, Type

import requests
from django.conf import settings
from django.utils.module_loading import import_string

from common.osu.enums import BeatmapStatus, Gamemode


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

    submission_date: datetime
    last_updated: datetime
    approval_date: datetime | None

    @classmethod
    def from_dict(cls, data: dict) -> "BeatmapData":
        return cls(
            beatmap_id=int(data["beatmap_id"]),
            set_id=int(data["beatmapset_id"]),
            gamemode=Gamemode(int(data["mode"])),
            status=BeatmapStatus(int(data["approved"])),
            artist=data["artist"],
            title=data["title"],
            difficulty_name=data["version"],
            creator_name=data["creator"],
            creator_id=data["creator_id"],
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


class AbstractOsuApiV1(ABC):
    @abstractmethod
    def get_beatmap(self, beatmap_id: int) -> BeatmapData | None:
        raise NotImplementedError()

    @abstractmethod
    def get_user_by_id(self, user_id: int, gamemode: Gamemode) -> dict | None:
        raise NotImplementedError()

    @abstractmethod
    def get_user_by_name(self, username: str, gamemode: Gamemode) -> dict | None:
        raise NotImplementedError()

    @abstractmethod
    def get_user_scores_for_beatmap(
        self, beatmap_id: int, user_id: int, gamemode: Gamemode
    ) -> list[dict]:
        raise NotImplementedError()

    @abstractmethod
    def get_user_best_scores(self, user_id: int, gamemode: Gamemode) -> list[dict]:
        raise NotImplementedError()

    @abstractmethod
    def get_user_recent_scores(self, user_id: int, gamemode: Gamemode) -> list[dict]:
        raise NotImplementedError()


class LiveOsuApiV1(AbstractOsuApiV1):
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
            return BeatmapData.from_dict(
                self.__get_legacy_endpoint("get_beatmaps", b=beatmap_id)[0]
            )
        except IndexError:
            return None

    def get_user_by_id(self, user_id: int, gamemode: Gamemode) -> dict | None:
        try:
            return self.__get_legacy_endpoint(
                "get_user", u=user_id, type="id", m=gamemode.value
            )[0]
        except IndexError:
            return None

    def get_user_by_name(self, username: str, gamemode: Gamemode) -> dict | None:
        try:
            return self.__get_legacy_endpoint(
                "get_user", u=username, type="string", m=gamemode.value
            )[0]
        except IndexError:
            return None

    def get_user_scores_for_beatmap(
        self, beatmap_id: int, user_id: int, gamemode: Gamemode
    ) -> list[dict]:
        return self.__get_legacy_endpoint(
            "get_scores", b=beatmap_id, u=user_id, type="id", m=gamemode.value
        )

    def get_user_best_scores(self, user_id: int, gamemode: Gamemode) -> list[dict]:
        return self.__get_legacy_endpoint(
            "get_user_best", u=user_id, type="id", m=gamemode.value, limit=100
        )

    def get_user_recent_scores(self, user_id: int, gamemode: Gamemode) -> list[dict]:
        return self.__get_legacy_endpoint(
            "get_user_recent", u=user_id, type="id", m=gamemode.value, limit=50
        )


class StubOsuApiV1(AbstractOsuApiV1):
    def __load_stub_data__(self, filename: str) -> dict:
        with open(
            os.path.join(os.path.dirname(__file__), "stubdata", "apiv1", filename)
        ) as fp:
            return json.load(fp)

    def get_beatmap(self, beatmap_id: int) -> BeatmapData | None:
        try:
            return BeatmapData.from_dict(
                self.__load_stub_data__("beatmaps.json")[str(beatmap_id)]
            )
        except KeyError:
            return None

    def get_user_by_id(self, user_id: int, gamemode: Gamemode) -> dict | None:
        try:
            return self.__load_stub_data__("users.json")[str(user_id)][
                str(gamemode.value)
            ]
        except KeyError:
            return None

    def get_user_by_name(self, username: str, gamemode: Gamemode):
        users = self.__load_stub_data__("users.json")

        gamemode_str = str(gamemode.value)

        try:
            return next(
                users[user][gamemode_str]
                for user in users
                if users[user][gamemode_str]["username"].lower() == username.lower()
            )
        except (KeyError, StopIteration):
            return None

    def get_user_scores_for_beatmap(
        self, beatmap_id: int, user_id: int, gamemode: Gamemode
    ) -> list[dict]:
        try:
            return self.__load_stub_data__("scores.json")[str(user_id)][
                str(gamemode.value)
            ][str(beatmap_id)]
        except KeyError:
            return []

    def get_user_best_scores(self, user_id: int, gamemode: Gamemode) -> list[dict]:
        try:
            return self.__load_stub_data__("user_best.json")[str(user_id)][
                str(gamemode.value)
            ]
        except KeyError:
            return []

    def get_user_recent_scores(self, user_id: int, gamemode: Gamemode) -> list[dict]:
        try:
            return self.__load_stub_data__("user_recent.json")[str(user_id)][
                str(gamemode.value)
            ]
        except KeyError:
            return []


OsuApiV1: Type[AbstractOsuApiV1] = import_string(settings.OSU_API_V1_CLASS)
