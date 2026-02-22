"""
UserProfile stores per-user fitness preferences and metadata.

The ``user_id`` is the UUID from Supabase Auth (the JWT ``sub`` claim) and
serves as the primary key — no Django User model is needed.
"""

from django.db import models


class UserProfile(models.Model):
    """
    Stores fitness goals, dietary preferences, body type info, and knowledge
    rank for a single Supabase-authenticated user.
    """

    class FitnessGoal(models.TextChoices):
        CUTTING = "cutting", "Cutting"
        BULKING = "bulking", "Bulking"
        MAINTENANCE = "maintenance", "Maintenance"

    class BodyType(models.TextChoices):
        ECTOMORPH = "ectomorph", "Ectomorph"
        MESOMORPH = "mesomorph", "Mesomorph"
        ENDOMORPH = "endomorph", "Endomorph"

    # Supabase auth UUID used directly as PK — no FK to Django's User model
    user_id = models.CharField(max_length=255, primary_key=True)
    display_name = models.CharField(max_length=150, blank=True, default="")
    email = models.EmailField(blank=True, default="")

    fitness_goal = models.CharField(
        max_length=20,
        choices=FitnessGoal.choices,
        default=FitnessGoal.MAINTENANCE,
    )
    dietary_preferences = models.JSONField(
        default=list,
        blank=True,
        help_text='List of dietary tags, e.g. ["vegan", "halal"]',
    )

    current_body_type = models.CharField(
        max_length=20,
        choices=BodyType.choices,
        blank=True,
        default="",
    )
    goal_body_type = models.CharField(
        max_length=20,
        choices=BodyType.choices,
        blank=True,
        default="",
    )

    # Education rank: 1 = Beginner, 2 = Intermediate, 3 = Advanced. 0 = not yet tested.
    knowledge_rank = models.IntegerField(default=0)

    calorie_target = models.IntegerField(default=2000)
    protein_target = models.IntegerField(default=150, help_text="Grams per day")
    carbs_target = models.IntegerField(default=200, help_text="Grams per day")
    fat_target = models.IntegerField(default=65, help_text="Grams per day")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.display_name or self.email or self.user_id
