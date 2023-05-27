from unittest.mock import Mock, create_autospec, patch

from celery import Task

from osuchan.celery import debug_task, task_failure_handler


@patch("osuchan.celery.ErrorReporter.report_error")
def test_task_failure_handler(report_error_mock: Mock):
    test_exception = Exception("testexception")
    task_mock = create_autospec(spec=Task)
    task_mock.name = "testtask"
    task_failure_handler(
        task_mock,
        "1",
        test_exception,
        ["testarg"],
        {"testkey", "testvalue"},
        None,
        None,
    )
    report_error_mock.assert_called_once()
    assert report_error_mock.call_args.args[0] == test_exception
    assert (
        report_error_mock.call_args.kwargs["title"]
        == f"Exception occured in task `testtask`"
    )
    assert "testarg" in report_error_mock.call_args.kwargs["extra_details"]
    assert "testkey" in report_error_mock.call_args.kwargs["extra_details"]
    assert "testvalue" in report_error_mock.call_args.kwargs["extra_details"]
