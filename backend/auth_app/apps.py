from importlib import import_module

from django.apps import AppConfig


class AuthAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "auth_app"
    verbose_name = "Authentication and Identity"

    def ready(self):
        import_module("auth_app.signals")
