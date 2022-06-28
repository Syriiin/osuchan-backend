import traceback

import httpx
from django.conf import settings


class DiscordErrorLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if settings.DISCORD_WEBHOOK_URL_ERROR_LOG == "":
            return

        error_report = f"Exception occured in request '{request.method} {request.get_full_path()}'\n\n"
        if request.method == "POST":
            error_report += f"POST data:\n{request.POST}\n\n"
        error_report += "Traceback:\n"
        error_report += "".join(traceback.format_tb(exception.__traceback__))
        error_report += f"{exception.__class__.__name__}: {exception}"

        httpx.post(
            settings.DISCORD_WEBHOOK_URL_ERROR_LOG,
            data={
                "content": f"Exception occured in request `{request.method} {request.get_full_path()}`\n`{exception.__class__.__name__}: {exception}`"
            },
            files={
                "upload-file": (
                    "error.log",
                    error_report.encode("utf8"),
                    "text/plain",
                )
            },
        )
