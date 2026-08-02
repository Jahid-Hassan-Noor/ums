from django.tasks import task

from caterer_app.service import initialize_accounts


@task
def initialize_canteen_allowances_task():
    result = initialize_accounts()
    return {
        **result,
        "month": result["month"].isoformat(),
    }
