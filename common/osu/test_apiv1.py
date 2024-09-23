import json
import os
from abc import abstractmethod
from unittest.mock import Mock, patch

import pytest
from requests import HTTPError

from common.osu.apiv1 import LiveOsuApiV1
from common.osu.enums import Gamemode


class TestLiveOsuApiV1:
    @pytest.fixture
    def osu_api_test_settings(self, settings):
        settings.OSU_API_V1_BASE_URL = "testbaseurl/"
        settings.OSU_API_V1_KEY = "testkey"

    @pytest.fixture
    def osu_api_v1(self):
        return LiveOsuApiV1()

    class TestResponse:
        @abstractmethod
        def json(self) -> dict | list: ...

        def raise_for_status(self):
            pass

    class BeatmapTestResponse(TestResponse):
        def json(self):
            with open(
                os.path.join(
                    os.path.dirname(__file__), "stubdata", "apiv1", "beatmaps.json"
                )
            ) as fp:
                return [json.load(fp)["307618"]]

    class UserTestResponse(TestResponse):
        def json(self):
            with open(
                os.path.join(
                    os.path.dirname(__file__), "stubdata", "apiv1", "users.json"
                )
            ) as fp:
                return [json.load(fp)["5701575"]["0"]]

    class ScoresTestResponse(TestResponse):
        def json(self):
            with open(
                os.path.join(
                    os.path.dirname(__file__), "stubdata", "apiv1", "scores.json"
                )
            ) as fp:
                return json.load(fp)["5701575"]["0"]["362949"]

    class UserBestTestResponse(TestResponse):
        def json(self):
            with open(
                os.path.join(
                    os.path.dirname(__file__), "stubdata", "apiv1", "user_best.json"
                )
            ) as fp:
                return json.load(fp)["5701575"]["0"]

    class UserRecentTestResponse(TestResponse):
        def json(self):
            with open(
                os.path.join(
                    os.path.dirname(__file__), "stubdata", "apiv1", "user_recent.json"
                )
            ) as fp:
                return json.load(fp)["5701575"]["0"]

    class EmptyTestResponse(TestResponse):
        def json(self):
            return []

    class ErrorTestResponse(EmptyTestResponse):
        def raise_for_status(self):
            raise HTTPError()

    @patch("common.osu.apiv1.requests.get", return_value=BeatmapTestResponse())
    def test_get_beatmap(
        self, get_mock: Mock, osu_api_v1: LiveOsuApiV1, osu_api_test_settings: None
    ):
        beatmap_data = osu_api_v1.get_beatmap(beatmap_id=1)
        assert beatmap_data is not None
        assert beatmap_data.title == "Songs Compilation"
        get_mock.assert_called_once_with(
            "testbaseurl/get_beatmaps", params={"b": 1, "k": "testkey"}
        )

    @patch("common.osu.apiv1.requests.get", return_value=UserTestResponse())
    def test_get_user_by_id(
        self, get_mock: Mock, osu_api_v1: LiveOsuApiV1, osu_api_test_settings: None
    ):
        user_data = osu_api_v1.get_user_by_id(1, Gamemode.STANDARD)
        assert user_data is not None
        assert user_data["username"] == "Syrin"
        get_mock.assert_called_once_with(
            "testbaseurl/get_user",
            params={"u": 1, "type": "id", "m": 0, "k": "testkey"},
        )

    @patch("common.osu.apiv1.requests.get", return_value=EmptyTestResponse())
    def test_get_user_by_id_not_found(
        self, get_mock: Mock, osu_api_v1: LiveOsuApiV1, osu_api_test_settings: None
    ):
        user_data = osu_api_v1.get_user_by_id(1, Gamemode.STANDARD)
        assert user_data is None

    @patch("common.osu.apiv1.requests.get", return_value=ErrorTestResponse())
    def test_get_user_by_id_error(
        self, get_mock: Mock, osu_api_v1: LiveOsuApiV1, osu_api_test_settings: None
    ):
        with pytest.raises(HTTPError):
            osu_api_v1.get_user_by_id(1, Gamemode.STANDARD)

    @patch("common.osu.apiv1.requests.get", return_value=UserTestResponse())
    def test_get_user_by_name(
        self, get_mock: Mock, osu_api_v1: LiveOsuApiV1, osu_api_test_settings: None
    ):
        user_data = osu_api_v1.get_user_by_name("testusername", Gamemode.STANDARD)
        assert user_data is not None
        assert user_data["username"] == "Syrin"
        get_mock.assert_called_once_with(
            "testbaseurl/get_user",
            params={"u": "testusername", "type": "string", "m": 0, "k": "testkey"},
        )

    @patch("common.osu.apiv1.requests.get", return_value=ScoresTestResponse())
    def test_get_user_scores_for_beatmap(
        self, get_mock: Mock, osu_api_v1: LiveOsuApiV1, osu_api_test_settings: None
    ):
        score_data = osu_api_v1.get_user_scores_for_beatmap(1, 2, Gamemode.STANDARD)[0]
        assert score_data["score"] == "3502092"
        get_mock.assert_called_once_with(
            "testbaseurl/get_scores",
            params={"b": 1, "u": 2, "type": "id", "m": 0, "k": "testkey"},
        )

    @patch("common.osu.apiv1.requests.get", return_value=UserBestTestResponse())
    def test_get_user_best_scores(
        self, get_mock: Mock, osu_api_v1: LiveOsuApiV1, osu_api_test_settings: None
    ):
        score_data = osu_api_v1.get_user_best_scores(1, Gamemode.STANDARD)[0]
        assert score_data["score"] == "137805806"
        get_mock.assert_called_once_with(
            "testbaseurl/get_user_best",
            params={"u": 1, "type": "id", "m": 0, "limit": 100, "k": "testkey"},
        )

    @patch("common.osu.apiv1.requests.get", return_value=UserRecentTestResponse())
    def test_get_user_recent_scores(
        self, get_mock: Mock, osu_api_v1: LiveOsuApiV1, osu_api_test_settings: None
    ):
        score_data = osu_api_v1.get_user_recent_scores(1, Gamemode.STANDARD)[0]
        assert score_data["score"] == "1881030"
        get_mock.assert_called_once_with(
            "testbaseurl/get_user_recent",
            params={"u": 1, "type": "id", "m": 0, "limit": 50, "k": "testkey"},
        )
