"""Background tasks for the accountant app (fines/charges)."""
import logging

from django.tasks import task

from accountant_app.fine_service import mark_overdue_fines

logger = logging.getLogger(__name__)


@task
def mark_overdue_fines_task():
    """
    Periodic task: mark pending fines whose due_date has passed as overdue.
    Schedule this to run hourly via Django-tasks or a cron job.
    """
    count = mark_overdue_fines()
    logger.info("mark_overdue_fines_task: flagged %d fines as overdue.", count)
    return {"overdue_fines_flagged": count}
