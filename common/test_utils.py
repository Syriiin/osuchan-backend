from unittest import TestCase

from common.utils import parse_float_or_none, parse_int_or_none


class GamemodeConverterTestCase(TestCase):
    def test_parse_int_or_none(self):
        self.assertEqual(parse_int_or_none("727"), 727)
        self.assertEqual(parse_int_or_none("hello"), None)

    def test_parse_float_or_none(self):
        self.assertEqual(parse_float_or_none("727.727"), 727.727)
        self.assertEqual(parse_float_or_none("hello"), None)
