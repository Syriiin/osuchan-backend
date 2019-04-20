# osu!chan related enums

from enum import IntEnum
    
class ScoreResult(IntEnum):
    PERFECT = 1
    NOBREAK = 2
    SLIDERBREAK = 4
    ONEMISS = 8
    ENDCHOKE = 16
    CLEAR = 32

    FC = PERFECT | NOBREAK
    CHOKE = SLIDERBREAK | ONEMISS | ENDCHOKE
