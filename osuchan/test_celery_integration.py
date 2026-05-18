import time
import uuid
from pathlib import Path

import pytest

from osuchan.celery import test_task

TEST_TIMEOUT_SECONDS = 5


@pytest.mark.integration
def test_worker_executes_task():
    task_id = str(uuid.uuid4())
    file_path = Path(f"tests/tmp/celery_test_{task_id}.txt")

    # fire off task
    test_task.apply_async(args=[task_id])

    # wait for task to complete and check result
    start_time = time.time()
    while time.time() - start_time < TEST_TIMEOUT_SECONDS:
        if file_path.exists():
            content = file_path.read_text()
            assert "completed" in content
            return
        time.sleep(0.5)

    pytest.fail(f"Task did not complete within {TEST_TIMEOUT_SECONDS} seconds")


@pytest.mark.integration
def test_task_priority_ordering():
    task_id_a = str(uuid.uuid4())
    task_id_b = str(uuid.uuid4())
    task_id_c = str(uuid.uuid4())

    file_path_a = Path(f"tests/tmp/celery_test_{task_id_a}.txt")
    file_path_b = Path(f"tests/tmp/celery_test_{task_id_b}.txt")
    file_path_c = Path(f"tests/tmp/celery_test_{task_id_c}.txt")

    # create backlog of tasks to ensure our tasks arent executed immediately
    for i in range(100):
        test_task.apply_async()

    # fire off tasks with different priorities (lower number = higher priority)
    test_task.apply_async(args=[task_id_c], priority=9)
    test_task.apply_async(args=[task_id_b], priority=5)
    test_task.apply_async(args=[task_id_a], priority=0)

    # wait for tasks to complete
    start_time = time.time()
    completed = {}
    while time.time() - start_time < TEST_TIMEOUT_SECONDS:
        if file_path_a.exists() and "a" not in completed:
            content = file_path_a.read_text()
            completed["a"] = float(content.split(":")[1])
        if file_path_b.exists() and "b" not in completed:
            content = file_path_b.read_text()
            completed["b"] = float(content.split(":")[1])
        if file_path_c.exists() and "c" not in completed:
            content = file_path_c.read_text()
            completed["c"] = float(content.split(":")[1])

        if len(completed) == 3:
            break
        time.sleep(0.5)

    # assert all tasks completed and in correct order
    assert len(completed) == 3, f"Only {len(completed)} tasks completed: {completed}"
    assert (
        completed["a"] < completed["b"] < completed["c"]
    ), f"Priority order incorrect: a={completed['a']}, b={completed['b']}, c={completed['c']}"


@pytest.mark.integration
def test_concurrent_tasks_complete():
    task_ids = [str(uuid.uuid4()) for _ in range(3)]
    file_paths = [Path(f"tests/tmp/celery_test_{tid}.txt") for tid in task_ids]

    # fire off multiple tasks at once
    for tid in task_ids:
        test_task.apply_async(args=[tid])

    # wait for all tasks to complete
    start_time = time.time()
    while time.time() - start_time < TEST_TIMEOUT_SECONDS:
        completed = sum(1 for fp in file_paths if fp.exists())
        if completed == 3:
            return
        time.sleep(0.5)

    pytest.fail(f"Not all tasks completed within {TEST_TIMEOUT_SECONDS} seconds")
