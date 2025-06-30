from rest_framework import permissions
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from ppraces.models import PPRace
from ppraces.serialisers import PPRaceSerialiser


class PPRaceDetail(APIView):
    """
    API endpoint for specific pp races
    """

    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get(self, request, pprace_id):
        try:
            leaderboard = PPRace.objects.get(id=pprace_id)
        except PPRace.DoesNotExist:
            raise NotFound("Leaderboard not found.")

        serialiser = PPRaceSerialiser(leaderboard)
        return Response(serialiser.data)
