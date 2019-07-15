from rest_framework import permissions

class BetaPermission(permissions.BasePermission):
    """
    Global permission check for beta testers.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_beta_tester
