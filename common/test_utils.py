from common.utils import parse_float_or_none, parse_int_or_none


def test_parse_int_or_none():
    assert parse_int_or_none("727") == 727
    assert parse_int_or_none("hello") == None


def test_parse_float_or_none():
    assert parse_float_or_none("727.727") == 727.727
    assert parse_float_or_none("hello") == None
