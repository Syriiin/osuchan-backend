from common.error_report import report_error


class DiscordErrorLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        extra_details = ""
        if request.method == "POST":
            extra_details += f"POST data:\n{request.POST}\n\n"

        report_error(
            exception,
            title=f"Exception occured in request `{request.method} {request.get_full_path()}`",
            extra_details=extra_details,
        )
