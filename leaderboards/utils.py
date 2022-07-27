from leaderboards.enums import LeaderboardAccessType


def get_leaderboard_type_string_from_leaderboard_access_type(
    leaderboard_access_type: LeaderboardAccessType,
):
    if leaderboard_access_type == LeaderboardAccessType.GLOBAL:
        return "global"
    else:
        return "community"
