import logging

from celery import Celery
from celery.signals import task_failure, worker_process_init
from prometheus_client import start_http_server

from common.error_reporter import ErrorReporter

app = Celery("osuchan")

logger = logging.getLogger(__name__)

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    logger.info("Request: {0!r}".format(self.request))


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


@worker_process_init.connect
def worker_init_handler(**kwargs):
    logger.info("Worker initialized, setting up prometheus metrics...")
    ports = range(9001, 9050)
    for port in ports:
        try:
            start_http_server(port)
            logger.info(f"Prometheus metrics server started on port {port}")
            break
        except OSError as e:
            pass
    else:
        logger.info("No available ports for Prometheus metrics server. Exiting worker.")
        raise RuntimeError("No available ports for Prometheus metrics server.")
