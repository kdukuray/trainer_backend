from django.apps import AppConfig


class UsersConfig(AppConfig):
    """User profiles and personal preferences."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "users"
