"""
MealLog stores each food item analyzed by Gemini from a photo.

The image is uploaded to Supabase Storage and its public URL stored here
alongside the AI-generated nutritional breakdown.
"""

from django.db import models


class MealLog(models.Model):
    """A single food item or meal logged via photo analysis."""

    user_id = models.CharField(max_length=255, db_index=True)

    food_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")

    calories = models.IntegerField(default=0)
    protein_g = models.FloatField(default=0)
    carbs_g = models.FloatField(default=0)
    fat_g = models.FloatField(default=0)
    fiber_g = models.FloatField(default=0)

    serving_size = models.CharField(max_length=100, blank=True, default="")
    nutritional_details = models.JSONField(
        default=dict,
        blank=True,
        help_text="Micronutrients: sodium_mg, sugar_g, vitamin_a_pct, etc.",
    )

    image_url = models.URLField(
        max_length=500,
        blank=True,
        default="",
        help_text="Public URL of the uploaded food photo in Supabase Storage",
    )

    logged_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self) -> str:
        return f"{self.food_name} — {self.calories} kcal"
