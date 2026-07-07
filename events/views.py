from collections import OrderedDict

from rest_framework import status
from rest_framework.exceptions import NotFound, ParseError, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from common.osu.enums import Gamemode
from common.utils import parse_int_or_none
from events.models import Event, EventLeaderboard
from events.serialisers import (
    EventAttendeeSerialiser,
    EventLeaderboardSerialiser,
    EventSerialiser,
)
from events.services import (
    add_event_attendee,
    create_event_leaderboard,
    delete_event_leaderboard,
    remove_event_attendee,
    update_event,
)
from profiles.models import OsuUser


class EventList(APIView):
    def get(self, request):
        limit = parse_int_or_none(request.query_params.get("limit", 20))
        offset = parse_int_or_none(request.query_params.get("offset", 0))
        if limit > 100:
            limit = 100

        events = Event.objects.order_by("-start_date")

        serialiser = EventSerialiser(events[offset : offset + limit], many=True)
        return Response(OrderedDict(count=events.count(), results=serialiser.data))


class EventDetail(APIView):
    def get(self, request, slug):
        try:
            event = Event.objects.get(slug=slug)
        except Event.DoesNotExist:
            raise NotFound("Event not found.")

        serialiser = EventSerialiser(event)
        return Response(serialiser.data)

    def patch(self, request, slug):
        osu_user_id = request.user.osu_user_id
        if osu_user_id is None:
            raise PermissionDenied("Must be authenticated with an osu! account.")

        try:
            event = Event.objects.get(slug=slug)
        except Event.DoesNotExist:
            raise NotFound("Event not found.")

        if not event.is_organiser(osu_user_id):
            raise PermissionDenied("Must be an organiser to edit this event.")

        update_event(
            event,
            name=request.data.get("name"),
            description=request.data.get("description"),
            logo=request.data.get("logo"),
            theme_colours=request.data.get("theme_colours"),
            start_date=request.data.get("start_date"),
            end_date=request.data.get("end_date"),
            creation_time=request.data.get("creation_time"),
        )

        serialiser = EventSerialiser(event)
        return Response(serialiser.data)


class EventAttendeeList(APIView):
    def get(self, request, slug):
        try:
            event = Event.objects.get(slug=slug)
        except Event.DoesNotExist:
            raise NotFound("Event not found.")

        limit = parse_int_or_none(request.query_params.get("limit", 5))
        offset = parse_int_or_none(request.query_params.get("offset", 0))
        if limit > 100:
            limit = 100

        attendees = event.event_attendees.select_related("user")

        serialiser = EventAttendeeSerialiser(
            attendees[offset : offset + limit], many=True
        )
        return Response(OrderedDict(count=attendees.count(), results=serialiser.data))

    def post(self, request, slug):
        osu_user_id = request.user.osu_user_id
        if osu_user_id is None:
            raise PermissionDenied("Must be authenticated with an osu! account.")

        try:
            event = Event.objects.get(slug=slug)
        except Event.DoesNotExist:
            raise NotFound("Event not found.")

        if not event.is_organiser(osu_user_id):
            raise PermissionDenied("Must be an organiser to add attendees.")

        user_id = request.data.get("user_id")
        if user_id is None:
            raise ParseError("Missing user_id parameter.")

        try:
            attendee, created = add_event_attendee(event, user_id)
        except OsuUser.DoesNotExist:
            raise NotFound("User not found.")

        serialiser = EventAttendeeSerialiser(attendee)
        return Response(serialiser.data, status=status.HTTP_201_CREATED)


class EventAttendeeDetail(APIView):
    def delete(self, request, slug, user_id):
        osu_user_id = request.user.osu_user_id
        if osu_user_id is None:
            raise PermissionDenied("Must be authenticated with an osu! account.")

        try:
            event = Event.objects.get(slug=slug)
        except Event.DoesNotExist:
            raise NotFound("Event not found.")

        if not event.is_organiser(osu_user_id):
            raise PermissionDenied("Must be an organiser to remove attendees.")

        remove_event_attendee(event, user_id)

        return Response(status=status.HTTP_204_NO_CONTENT)


class EventLeaderboardList(APIView):
    def get(self, request, slug):
        try:
            event = Event.objects.get(slug=slug)
        except Event.DoesNotExist:
            raise NotFound("Event not found.")

        event_leaderboards = event.event_leaderboards.select_related(
            "leaderboard", "leaderboard__score_filter"
        )

        serialiser = EventLeaderboardSerialiser(event_leaderboards, many=True)
        return Response(serialiser.data)

    def post(self, request, slug):
        osu_user_id = request.user.osu_user_id
        if osu_user_id is None:
            raise PermissionDenied("Must be authenticated with an osu! account.")

        try:
            event = Event.objects.get(slug=slug)
        except Event.DoesNotExist:
            raise NotFound("Event not found.")

        if not event.is_organiser(osu_user_id):
            raise PermissionDenied("Must be an organiser to manage leaderboards.")

        gamemode = request.data.get("gamemode")
        if gamemode is None:
            raise ParseError("Missing gamemode parameter.")

        name = request.data.get("name")
        if name is None:
            raise ParseError("Missing name parameter.")

        event_leaderboard = create_event_leaderboard(
            event,
            gamemode=Gamemode(gamemode),
            name=name,
        )

        serialiser = EventLeaderboardSerialiser(event_leaderboard)
        return Response(serialiser.data, status=status.HTTP_201_CREATED)


class EventLeaderboardDetail(APIView):
    def delete(self, request, slug, event_leaderboard_id):
        osu_user_id = request.user.osu_user_id
        if osu_user_id is None:
            raise PermissionDenied("Must be authenticated with an osu! account.")

        try:
            event = Event.objects.get(slug=slug)
        except Event.DoesNotExist:
            raise NotFound("Event not found.")

        if not event.is_organiser(osu_user_id):
            raise PermissionDenied("Must be an organiser to manage leaderboards.")

        try:
            event_leaderboard = EventLeaderboard.objects.get(
                event=event, id=event_leaderboard_id
            )
        except EventLeaderboard.DoesNotExist:
            raise NotFound("Event leaderboard not found.")

        delete_event_leaderboard(event_leaderboard)

        return Response(status=status.HTTP_204_NO_CONTENT)
