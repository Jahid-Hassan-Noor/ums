from django.tasks import task

from chatbot_app.search_indexer import rebuild_search_index


@task
def rebuild_chatbot_search_index_task(domains=None, clear=False, dry_run=False):
    return rebuild_search_index(
        domains=domains,
        clear=clear,
        dry_run=dry_run,
    )
