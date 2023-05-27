from unittest.mock import Mock, patch

import pytest

from common.osu.apiv1 import LiveOsuApiV1


class TestLiveOsuApiV1:
    @pytest.fixture
    def osu_api_test_settings(self, settings):
        settings.OSU_API_V1_BASE_URL = "testbaseurl/"
        settings.OSU_API_V1_KEY = "testkey"

    @pytest.fixture
    def osu_api_v1(self):
        return LiveOsuApiV1()

    class TestResponse:
        def json(self):
            return [{"name": "test"}]

    class EmptyTestResponse:
        def json(self):
            return []

    @patch("common.osu.apiv1.requests.get", return_value=TestResponse())
    def test_get_beatmaps(
        self, get_mock: Mock, osu_api_v1: LiveOsuApiV1, osu_api_test_settings: None
    ):
        beatmap_data = osu_api_v1.get_beatmaps(beatmap_id=1)[0]
        assert beatmap_data["name"] == "test"
        get_mock.assert_called_once_with(
            "testbaseurl/get_beatmaps", params={"b": 1, "k": "testkey"}
        )

    @patch("common.osu.apiv1.requests.get", return_value=TestResponse())
    def test_get_user(
        self, get_mock: Mock, osu_api_v1: LiveOsuApiV1, osu_api_test_settings: None
    ):
        user_data = osu_api_v1.get_user(user_id=1)
        assert user_data is not None
        assert user_data["name"] == "test"
        get_mock.assert_called_once_with(
            "testbaseurl/get_user", params={"u": 1, "type": "id", "k": "testkey"}
        )

    @patch("common.osu.apiv1.requests.get", return_value=EmptyTestResponse())
    def test_get_user_not_found(
        self, get_mock: Mock, osu_api_v1: LiveOsuApiV1, osu_api_test_settings: None
    ):
        user_data = osu_api_v1.get_user(user_id=1)
        assert user_data is None

    @patch("common.osu.apiv1.requests.get", return_value=TestResponse())
    def test_get_scores(
        self, get_mock: Mock, osu_api_v1: LiveOsuApiV1, osu_api_test_settings: None
    ):
        score_data = osu_api_v1.get_scores(beatmap_id=1)[0]
        assert score_data["name"] == "test"
        get_mock.assert_called_once_with(
            "testbaseurl/get_scores", params={"b": 1, "type": "id", "k": "testkey"}
        )

    @patch("common.osu.apiv1.requests.get", return_value=TestResponse())
    def test_get_user_best(
        self, get_mock: Mock, osu_api_v1: LiveOsuApiV1, osu_api_test_settings: None
    ):
        score_data = osu_api_v1.get_user_best(user_id=1)[0]
        assert score_data["name"] == "test"
        get_mock.assert_called_once_with(
            "testbaseurl/get_user_best", params={"u": 1, "type": "id", "k": "testkey"}
        )

    @patch("common.osu.apiv1.requests.get", return_value=TestResponse())
    def test_get_user_recent(
        self, get_mock: Mock, osu_api_v1: LiveOsuApiV1, osu_api_test_settings: None
    ):
        score_data = osu_api_v1.get_user_recent(user_id=1)[0]
        assert score_data["name"] == "test"
        get_mock.assert_called_once_with(
            "testbaseurl/get_user_recent", params={"u": 1, "type": "id", "k": "testkey"}
        )
