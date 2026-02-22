"""
MealPlan stores AI-generated daily or weekly meal plans.

``plan_data`` holds the structured JSON produced by Gemini so the frontend
can render days, meals, portions, and macro breakdowns.
"""

from django.db import models


class MealPlan(models.Model):
    """A single AI-generated meal plan belonging to one user."""

    class PlanType(models.TextChoices):
        DAILY = "daily", "Daily"
        WEEKLY = "weekly", "Weekly"

    user_id = models.CharField(max_length=255, db_index=True)

    plan_type = models.CharField(
        max_length=10,
        choices=PlanType.choices,
        default=PlanType.DAILY,
    )
    fitness_goal = models.CharField(max_length=20, blank=True, default="")
    dietary_preferences = models.JSONField(default=list, blank=True)
    calorie_target = models.IntegerField(default=2000)
    protein_target = models.IntegerField(default=150)
    carbs_target = models.IntegerField(default=200)
    fat_target = models.IntegerField(default=65)
    favorite_foods = models.TextField(blank=True, default="")

    # The full Gemini-generated plan stored as structured JSON
    plan_data = models.JSONField(
        default=dict,
        help_text="Structured meal plan with days, meals, portions, and macros",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self) -> str:
        plan_name = self.plan_data.get("plan_name", "Meal Plan")
        return f"{plan_name} ({self.plan_type}) — {self.user_id[:8]}"
