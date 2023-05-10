from common.osu.utils import (
    get_gamemode_from_gamemode_string,
    get_gamemode_string_from_gamemode,
)


class GamemodeConverter:
    regex = r"([0-3]|osu|taiko|catch|mania)"

    def to_python(self, value):
        return get_gamemode_from_gamemode_string(value)

    def to_url(self, value):
        return get_gamemode_string_from_gamemode(value)


class LeaderboardTypeConverter:
    regex = r"(global|community)"

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value
