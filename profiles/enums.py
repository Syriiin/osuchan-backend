# profiles related enums

from enum import IntEnum


class ScoreResult(IntEnum):
    PERFECT = 1
    NO_BREAK = 2
    SLIDER_BREAK = 4
    ONE_MISS = 8
    END_CHOKE = 16
    CLEAR = 32

    FULL_COMBO = PERFECT | NO_BREAK
    CHOKE = SLIDER_BREAK | ONE_MISS | END_CHOKE


class ScoreSet(IntEnum):
    NORMAL = 0
    NEVER_CHOKE = 1
    ALWAYS_FULL_COMBO = 2


class AllowedBeatmapStatus(IntEnum):
    ANY = 0
    RANKED_ONLY = 1  # ranked + approved
    LOVED_ONLY = 2
