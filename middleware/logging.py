import traceback

import httpx
from django.conf import settings


class DiscordErrorLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        exception_string = f"Exception occured in request '{request.method} {request.get_full_path()}':\n"
        exception_string += "".join(traceback.format_tb(exception.__traceback__))
        exception_string += f"{exception.__class__.__name__}: {exception}"

        httpx.post(
            settings.DISCORD_WEBHOOK_URL_ERROR_LOG,
            files={
                "upload-file": (
                    "error.log",
                    exception_string.encode("utf8"),
                    "text/plain",
                )
            },
        )
