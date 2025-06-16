# osu! related enums

from enum import IntEnum, StrEnum

# Mods
# https://github.com/ppy/osu-api/wiki#mods


class Mods(IntEnum):
    NONE = 0
    NOFAIL = 1
    EASY = 2
    TOUCH_DEVICE = 4
    HIDDEN = 8
    HARDROCK = 16
    SUDDEN_DEATH = 32
    DOUBLETIME = 64
    RELAX = 128
    HALFTIME = 256
    NIGHTCORE = 512
    FLASHLIGHT = 1024
    AUTO = 2048
    SPUN_OUT = 4096
    AUTOPILOT = 8192
    PERFECT = 16384
    KEY_4 = 32768
    KEY_5 = 65536
    KEY_6 = 131072
    KEY_7 = 262144
    KEY_8 = 524288
    FADE_IN = 1048576
    RANDOM = 2097152
    CINEMA = 4194304
    TARGET_PRACTICE = 8388608
    KEY_9 = 16777216
    KEY_COOP = 33554432
    KEY_1 = 67108864
    KEY_2 = 134217728
    KEY_3 = 268435456
    SCORE_V2 = 536870912
    MIRROR = 1073741824

    KEY_MOD = (
        KEY_1 | KEY_2 | KEY_3 | KEY_4 | KEY_5 | KEY_6 | KEY_7 | KEY_8 | KEY_9 | KEY_COOP
    )
    FREEMOD_ALLOWED = (
        NOFAIL
        | EASY
        | HIDDEN
        | HARDROCK
        | SUDDEN_DEATH
        | FLASHLIGHT
        | FADE_IN
        | RELAX
        | AUTOPILOT
        | SPUN_OUT
        | KEY_MOD
    )
    SCORE_INCREASING = HIDDEN | HARDROCK | DOUBLETIME | FLASHLIGHT | AUTOPILOT | FADE_IN

    SPEED_CHANGING = DOUBLETIME | HALFTIME | NIGHTCORE
    MAP_CHANGING = SPEED_CHANGING | HARDROCK | EASY
    UNRANKED = (
        RELAX | AUTO | AUTOPILOT | KEY_1 | KEY_2 | KEY_3 | KEY_COOP | RANDOM | SCORE_V2
    )


class NewMods(StrEnum):
    NOFAIL = "NF"
    EASY = "EZ"
    TOUCH_DEVICE = "TD"
    HIDDEN = "HD"
    HARDROCK = "HR"
    SUDDEN_DEATH = "SD"
    DOUBLETIME = "DT"
    RELAX = "RX"
    HALFTIME = "HT"
    NIGHTCORE = "NC"
    FLASHLIGHT = "FL"
    AUTO = "AUTO"
    SPUN_OUT = "SO"
    AUTOPILOT = "AP"
    PERFECT = "PF"
    KEY_4 = "4K"
    KEY_5 = "5K"
    KEY_6 = "6K"
    KEY_7 = "7K"
    KEY_8 = "8K"
    FADE_IN = "FI"
    RANDOM = "RN"
    CINEMA = "CN"
    TARGET_PRACTICE = "TP"
    KEY_9 = "9K"
    KEY_COOP = "COOP"
    KEY_1 = "1K"
    KEY_2 = "2K"
    KEY_3 = "3K"
    SCORE_V2 = "V2"
    MIRROR = "MI"
    CLASSIC = "CL"
    BLINDS = "BL"
    ACCURACY_CHALLENGE = "AC"
    DAYCORE = "DC"
    TRACING = "TC"
    MUTED = "MU"
    NO_SCOPE = "NS"


# Gamemodes


class Gamemode(IntEnum):
    STANDARD = 0
    TAIKO = 1
    CATCH = 2
    MANIA = 3


# Beatmap Status


class BeatmapStatus(IntEnum):
    GRAVEYARD = -2
    WIP = -1
    PENDING = 0
    RANKED = 1
    APPROVED = 2
    QUALIFIED = 3
    LOVED = 4
