"""Serializers for meal log data."""

from rest_framework import serializers

from .models import MealLog


class MealLogListSerializer(serializers.ModelSerializer):
    """Compact serializer for the meal log list — name, calories, and date."""

    class Meta:
        model = MealLog
        fields = ["id", "food_name", "calories", "logged_at"]


class MealLogDetailSerializer(serializers.ModelSerializer):
    """Full serializer for the meal log detail view with all nutritional data."""

    class Meta:
        model = MealLog
        fields = [
            "id",
            "user_id",
            "food_name",
            "description",
            "calories",
            "protein_g",
            "carbs_g",
            "fat_g",
            "fiber_g",
            "serving_size",
            "nutritional_details",
            "image_url",
            "logged_at",
        ]
        read_only_fields = fields
