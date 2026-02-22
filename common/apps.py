from django.apps import AppConfig


class CommonConfig(AppConfig):
    """Shared utilities: authentication, pagination, and helpers."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "common"
