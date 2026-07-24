from datetime import datetime

from django.db import transaction

from common.osu.difficultycalculator import get_default_difficulty_calculator_class
from common.osu.enums import Gamemode
from events.enums import BeatmapChallengeType
from events.models import (
    BeatmapChallenge,
    BeatmapChallengeScore,
    Event,
    EventAttendee,
    EventLeaderboard,
)
from leaderboards.enums import LeaderboardAccessType
from leaderboards.models import Leaderboard, Membership
from leaderboards.services import create_membership, delete_membership
from profiles.enums import ScoreMutation, ScoreSet
from profiles.models import OsuUser, Score, ScoreFilter
from profiles.services import refresh_user_from_api


@transaction.atomic
def update_event(
    event: Event,
    name: str | None = None,
    description: str | None = None,
    logo: str | None = None,
    theme_colours: dict | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    creation_time: datetime | None = None,
) -> Event:
    """Partially update an event's fields and cascade date changes to its score filters."""
    if name is not None:
        event.name = name
    if description is not None:
        event.description = description
    if logo is not None:
        event.logo = logo
    if theme_colours is not None:
        event.theme_colours = theme_colours
    if start_date is not None:
        event.start_date = start_date
    if end_date is not None:
        event.end_date = end_date
    if creation_time is not None:
        event.creation_time = creation_time
    event.save()

    if start_date is not None or end_date is not None:
        for event_leaderboard in event.event_leaderboards.select_related(
            "leaderboard", "leaderboard__score_filter"
        ):
            score_filter = event_leaderboard.leaderboard.score_filter
            if start_date is not None:
                score_filter.oldest_score_date = start_date
            if end_date is not None:
                score_filter.newest_score_date = end_date
            score_filter.save()

        # TODO: fix circular import
        from events.tasks import refresh_event_leaderboards

        transaction.on_commit(lambda: refresh_event_leaderboards.delay(event.id))

    return event


@transaction.atomic
def create_event_leaderboard(
    event: Event,
    gamemode: Gamemode,
    name: str,
) -> EventLeaderboard:
    """Create a leaderboard and membership for each attendee scoped to an event."""
    score_filter = ScoreFilter(
        oldest_score_date=event.start_date,
        newest_score_date=event.end_date,
    )
    score_filter.save()

    leaderboard = Leaderboard(
        gamemode=gamemode,
        score_set=ScoreSet.NORMAL,
        access_type=LeaderboardAccessType.PUBLIC,
        name=name,
        description="",
        icon_url=event.logo,
        custom_colours=event.theme_colours,
        allow_past_scores=True,
        archived=False,
        is_event=True,
        member_count=0,
        notification_discord_webhook_url="",
        calculator_engine=get_default_difficulty_calculator_class(gamemode).engine(),
        primary_performance_value="total",
        owner=None,
        score_filter=score_filter,
        notification_settings={
            "top_score": False,
            "top_player": False,
            "podium": False,
            "player_first_score": False,
            "player_top_score": False,
            "top_10_score": False,
        },
    )
    leaderboard.save()

    event_leaderboard = EventLeaderboard.objects.create(
        event=event, leaderboard=leaderboard
    )

    for attendee in event.event_attendees.select_related("user"):
        create_membership(leaderboard.id, attendee.user_id)

    return event_leaderboard


@transaction.atomic
def add_event_attendee(event: Event, user_id: int) -> tuple[EventAttendee, bool]:
    """Add a user as an attendee and auto-subscribe them to all event leaderboards."""
    if not OsuUser.objects.filter(id=user_id).exists():
        refresh_user_from_api(user_id=user_id)
        if not OsuUser.objects.filter(id=user_id).exists():
            raise OsuUser.DoesNotExist(
                f"User with id {user_id} not found even after attempting to update."
            )

    attendee, created = EventAttendee.objects.get_or_create(
        event=event, user_id=user_id
    )
    if created:
        for event_leaderboard in event.event_leaderboards.select_related("leaderboard"):
            create_membership(event_leaderboard.leaderboard_id, user_id)
    return attendee, created


@transaction.atomic
def remove_event_attendee(event: Event, user_id: int) -> None:
    """Remove a user's attendee status and all event leaderboard memberships."""
    for event_leaderboard in event.event_leaderboards.select_related("leaderboard"):
        try:
            membership = Membership.objects.get(
                leaderboard=event_leaderboard.leaderboard_id, user_id=user_id
            )
            delete_membership(membership)
        except Membership.DoesNotExist:
            pass
    EventAttendee.objects.filter(event=event, user_id=user_id).delete()


@transaction.atomic
def delete_event_leaderboard(event_leaderboard: EventLeaderboard) -> None:
    """Delete an event leaderboard and its underlying leaderboard and score filter."""
    leaderboard = event_leaderboard.leaderboard
    score_filter = leaderboard.score_filter
    leaderboard.delete()
    score_filter.delete()


@transaction.atomic
def update_attendee_challenge_scores(
    beatmap_challenge: BeatmapChallenge, user_id: int
) -> None:
    """Update the best score for a given beatmap challenge for a given attendee"""
    scores = Score.objects.filter(
        user_stats__user_id=user_id,
        beatmap_id=beatmap_challenge.beatmap_id,
        gamemode=beatmap_challenge.gamemode,
        mutation=ScoreMutation.NONE,
        date__gte=beatmap_challenge.event.start_date,
        date__lte=beatmap_challenge.event.end_date,
    )

    if beatmap_challenge.challenge_type == BeatmapChallengeType.BEST_COMBO:
        best_score = scores.order_by("-best_combo", "date").first()
    elif beatmap_challenge.challenge_type == BeatmapChallengeType.LOWEST_MISS_COUNT:
        best_score = scores.order_by("count_miss", "date").first()
    else:
        best_score = scores.order_by("-date").first()

    if best_score is not None:
        BeatmapChallengeScore.objects.update_or_create(
            challenge=beatmap_challenge,
            user_id=user_id,
            defaults={"score": best_score},
        )
    else:
        BeatmapChallengeScore.objects.filter(
            challenge=beatmap_challenge, user_id=user_id
        ).delete()
