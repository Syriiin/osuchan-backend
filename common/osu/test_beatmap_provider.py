from unittest.mock import Mock, patch

import pytest

from common.osu.beatmap_provider import LiveBeatmapProvider


class TestLiveBeatmapProvider:
    @pytest.fixture
    def osu_api_test_settings(self, settings):
        settings.BEATMAP_DL_URL = "testbaseurl/"
        settings.BEATMAP_CACHE_PATH = "testcachepath/"

    @pytest.fixture
    def beatmap_provider(self):
        return LiveBeatmapProvider()

    @patch("common.osu.beatmap_provider.os.path.isfile", return_value=True)
    def test_get_beatmap_file_exists(
        self,
        isfile_mock: Mock,
        beatmap_provider: LiveBeatmapProvider,
        osu_api_test_settings,
    ):
        assert beatmap_provider.get_beatmap_file(1) == "testcachepath/1"
        isfile_mock.assert_called_once()

    @patch("common.osu.beatmap_provider.urllib.request.urlretrieve")
    @patch("common.osu.beatmap_provider.os.path.isfile", return_value=False)
    def test_get_beatmap_file_not_exists(
        self,
        isfile_mock: Mock,
        urlretrieve_mock: Mock,
        beatmap_provider: LiveBeatmapProvider,
        osu_api_test_settings,
    ):
        assert beatmap_provider.get_beatmap_file(1) == "testcachepath/1"
        isfile_mock.assert_called_once()
        urlretrieve_mock.assert_called_once_with("testbaseurl/1", "testcachepath/1")
