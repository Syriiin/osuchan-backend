from unittest import TestCase
from unittest.mock import Mock, patch

from common.utils import get_beatmap_path, parse_float_or_none, parse_int_or_none


class UtilsTestCase(TestCase):
    @patch("common.utils.os.path.isfile", return_value=True)
    def test_get_beatmap_path_exists(self, isfile_mock: Mock):
        self.assertEqual(get_beatmap_path("1"), "/app/beatmaps/1")
        isfile_mock.assert_called_once()

    @patch("common.utils.urllib.request.urlretrieve")
    @patch("common.utils.os.path.isfile", return_value=False)
    def test_get_beatmap_path_not_exists(
        self, isfile_mock: Mock, urlretrieve_mock: Mock
    ):
        self.assertEqual(get_beatmap_path("1"), "/app/beatmaps/1")
        isfile_mock.assert_called_once()
        urlretrieve_mock.assert_called_once()

    def test_parse_int_or_none(self):
        self.assertEqual(parse_int_or_none("727"), 727)
        self.assertEqual(parse_int_or_none("hello"), None)

    def test_parse_float_or_none(self):
        self.assertEqual(parse_float_or_none("727.727"), 727.727)
        self.assertEqual(parse_float_or_none("hello"), None)
