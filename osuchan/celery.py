import os
import traceback as tb

import httpx
from celery import Celery
from celery.signals import task_failure
from django.conf import settings

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "osuchan.settings")

app = Celery("osuchan")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print("Request: {0!r}".format(self.request))


@task_failure.connect
def task_failure_handler(
    sender,
    task_id,
    exception,
    args,
    kwargs,
    traceback,
    einfo,
    **akwargs,
):
    exception_string = f'Exception occured in task "{sender.name}":\n'
    exception_string += "".join(tb.format_tb(traceback))
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
