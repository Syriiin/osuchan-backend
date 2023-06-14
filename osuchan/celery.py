from celery import Celery
from celery.signals import task_failure

from common.error_reporter import ErrorReporter

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
    extra_details = f"args:\n{args}\n\n"
    extra_details += f"kwargs:\n{kwargs}\n\n"

    error_reporter = ErrorReporter()
    error_reporter.report_error(
        exception,
        title=f"Exception occured in task `{sender.name}`",
        extra_details=extra_details,
    )
