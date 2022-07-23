from datetime import datetime, timezone

from django.http import HttpRequest


class LastActiveMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        if request.user.is_authenticated:
            request.user.last_active = datetime.now(tz=timezone.utc)
            request.user.save()

        return self.get_response(request)
