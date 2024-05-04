import traceback
from abc import ABC, abstractmethod
from typing import Type

import httpx
from django.conf import settings
from django.utils.module_loading import import_string


class AbstractErrorReporter(ABC):
    @abstractmethod
    def report_error(
        self, exception: Exception, title: str = "", extra_details: str = ""
    ):
        raise NotImplementedError()


class DiscordErrorReporter(AbstractErrorReporter):
    def report_error(
        self, exception: Exception, title: str = "", extra_details: str = ""
    ) -> None:
        if settings.DISCORD_WEBHOOK_URL_ERROR_LOG == "":
            return

        error_report = ""

        if title != "":
            error_report = f"{title}\n"
        if extra_details != "":
            error_report += f"{extra_details}\n"

        error_report += "Traceback:\n"
        error_report += "".join(traceback.format_tb(exception.__traceback__))
        error_report += f"{exception.__class__.__name__}: {exception}"

        httpx.post(
            settings.DISCORD_WEBHOOK_URL_ERROR_LOG,
            data={"content": f"`{exception.__class__.__name__}: {exception}`"},
            files={
                "upload-file": (
                    "error.log",
                    error_report.encode("utf8"),
                    "text/plain",
                )
            },
        )


class DummyErrorReporter(AbstractErrorReporter):
    def report_error(
        self, exception: Exception, title: str = "", extra_details: str = ""
    ):
        raise exception


ErrorReporter: Type[AbstractErrorReporter] = import_string(
    settings.ERROR_REPORTER_CLASS
)
