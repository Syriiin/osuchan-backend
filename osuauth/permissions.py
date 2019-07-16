from rest_framework import permissions

from django.conf import settings

class BetaPermission(permissions.BasePermission):
    """
    Global permission check for beta testers.
    Allow if BETA is disabled, or user is a beta tester.
    """

    def has_permission(self, request, view):
        return not settings.BETA or (request.user.is_authenticated and request.user.is_beta_tester)
