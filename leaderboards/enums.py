# leaderboards related enums

from enum import IntEnum
    
class LeaderboardAccessType(IntEnum):
    GLOBAL = 0
    PUBLIC = 1
    PUBLIC_INVITE_ONLY = 2
    PRIVATE = 3
