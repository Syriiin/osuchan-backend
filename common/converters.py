from common.osu.enums import Gamemode


class GamemodeConverter:
    regex = r"([0-3]|osu|taiko|catch|mania)"

    def to_python(self, value):
        try:
            return Gamemode(int(value))
        except ValueError:
            if value == "osu":
                return Gamemode.STANDARD
            elif value == "taiko":
                return Gamemode.TAIKO
            elif value == "catch":
                return Gamemode.CATCH
            elif value == "mania":
                return Gamemode.MANIA

    def to_url(self, value):
        return value


class LeaderboardTypeConverter:
    regex = r"(global|community)"

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value
