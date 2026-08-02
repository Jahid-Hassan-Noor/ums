from uuid import uuid4

from django.tasks.backends.base import BaseTaskBackend
from django.tasks.base import TaskResult, TaskResultStatus
from django.tasks.signals import task_enqueued
from django.utils import timezone

from core.celery import app as celery_app


class CeleryTaskBackend(BaseTaskBackend):
    """Queue Django Tasks for execution by the project's Celery workers."""

    supports_defer = True

    def enqueue(self, task, args, kwargs):
        self.validate_task(task)

        enqueued_at = timezone.now()
        task_result = TaskResult(
            task=task,
            id=uuid4().hex,
            status=TaskResultStatus.READY,
            enqueued_at=enqueued_at,
            started_at=None,
            last_attempted_at=None,
            finished_at=None,
            args=args,
            kwargs=kwargs,
            backend=self.alias,
            errors=[],
            worker_ids=[],
        )
        celery_app.send_task(
            self.options.get("TASK_NAME", "core.execute_django_task"),
            kwargs={
                "task_path": task.module_path,
                "args": task_result.args,
                "kwargs": task_result.kwargs,
                "enqueued_at": enqueued_at.isoformat(),
            },
            task_id=task_result.id,
            queue=task.queue_name,
            eta=task.run_after,
        )
        task_enqueued.send(type(self), task_result=task_result)
        return task_result
