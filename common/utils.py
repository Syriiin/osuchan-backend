def parse_int_or_none(input):
    try:
        return int(input)
    except (ValueError, TypeError):
        return None


def parse_float_or_none(input):
    try:
        return float(input)
    except (ValueError, TypeError):
        return None
