import logging

from django.tasks import task

from admin_app.services.backups import send_monthly_backup_email


logger = logging.getLogger(__name__)


@task
def send_monthly_database_backup_email_task():
    result = send_monthly_backup_email()
    logger.info("send_monthly_database_backup_email_task: %s", result)
    return result

