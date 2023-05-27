from unittest.mock import Mock, patch

from common.utils import get_beatmap_path, parse_float_or_none, parse_int_or_none


@patch("common.utils.os.path.isfile", return_value=True)
def test_get_beatmap_path_exists(isfile_mock: Mock):
    assert get_beatmap_path("1") == "/app/beatmaps/1"
    isfile_mock.assert_called_once()


@patch("common.utils.urllib.request.urlretrieve")
@patch("common.utils.os.path.isfile", return_value=False)
def test_get_beatmap_path_not_exists(isfile_mock: Mock, urlretrieve_mock: Mock):
    assert get_beatmap_path("1"), "/app/beatmaps/1"
    isfile_mock.assert_called_once()
    urlretrieve_mock.assert_called_once()


def test_parse_int_or_none():
    assert parse_int_or_none("727") == 727
    assert parse_int_or_none("hello") == None


def test_parse_float_or_none():
    assert parse_float_or_none("727.727") == 727.727
    assert parse_float_or_none("hello") == None
