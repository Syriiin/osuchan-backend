# leaderboards related enums

from enum import IntEnum
    
class AllowedBeatmapStatus(IntEnum):
    ANY = 0
    RANKED_ONLY = 1     # ranked + approved
    LOVED_ONLY = 2
    
class LeaderboardAccessType(IntEnum):
    GLOBAL = 0
    PUBLIC = 1
    PUBLIC_INVITE_ONLY = 2
    PRIVATE = 3
