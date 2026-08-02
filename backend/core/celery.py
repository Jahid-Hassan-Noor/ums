import os
from datetime import datetime
from traceback import format_exception

from celery import Celery
from django.tasks import Task
from django.tasks.base import TaskContext, TaskError, TaskResult, TaskResultStatus
from django.tasks.signals import task_finished, task_started
from django.utils import timezone
from django.utils.json import normalize_json
from django.utils.module_loading import import_string


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("core")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


def _load_django_task(task_path):
    django_task = import_string(task_path)
    if not isinstance(django_task, Task):
        raise TypeError(f"{task_path!r} is not a Django Task.")
    return django_task


@app.task(name="core.enqueue_django_task", ignore_result=True)
def enqueue_django_task(task_path, args=None, kwargs=None):
    """Let Celery Beat enqueue a Django Task through its configured backend."""

    task_result = _load_django_task(task_path).enqueue(
        *(args or []),
        **(kwargs or {}),
    )
    return task_result.id


@app.task(name="core.execute_django_task", bind=True, acks_late=True)
def execute_django_task(
    celery_task,
    task_path,
    args=None,
    kwargs=None,
    enqueued_at=None,
):
    """Execute one Django Task claimed from the Celery broker."""

    django_task = _load_django_task(task_path)
    started_at = timezone.now()
    task_result = TaskResult(
        task=django_task,
        id=celery_task.request.id,
        status=TaskResultStatus.RUNNING,
        enqueued_at=datetime.fromisoformat(enqueued_at) if enqueued_at else None,
        started_at=started_at,
        last_attempted_at=started_at,
        finished_at=None,
        args=args or [],
        kwargs=kwargs or {},
        backend=django_task.backend,
        errors=[],
        worker_ids=[celery_task.request.hostname or "celery"],
    )
    task_started.send(type(django_task.get_backend()), task_result=task_result)

    try:
        if django_task.takes_context:
            return_value = django_task.call(
                TaskContext(task_result=task_result),
                *task_result.args,
                **task_result.kwargs,
            )
        else:
            return_value = django_task.call(*task_result.args, **task_result.kwargs)
        object.__setattr__(task_result, "_return_value", normalize_json(return_value))
        object.__setattr__(task_result, "status", TaskResultStatus.SUCCESSFUL)
        return task_result.return_value
    except KeyboardInterrupt:
        raise
    except BaseException as error:
        exception_type = type(error)
        task_result.errors.append(
            TaskError(
                exception_class_path=(
                    f"{exception_type.__module__}.{exception_type.__qualname__}"
                ),
                traceback="".join(format_exception(error)),
            )
        )
        object.__setattr__(task_result, "status", TaskResultStatus.FAILED)
        raise
    finally:
        object.__setattr__(task_result, "finished_at", timezone.now())
        task_finished.send(type(django_task.get_backend()), task_result=task_result)
