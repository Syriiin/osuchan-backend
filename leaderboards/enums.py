# leaderboards related enums

from enum import IntEnum
    
class AllowedBeatmapStatus(IntEnum):
    ANY = 0
    RANKED_ONLY = 1     # ranked + approved
    LOVED_ONLY = 2
    
class LeaderboardVisibility(IntEnum):
    GLOBAL = 0
    PUBLIC = 1
    PRIVATE = 2
