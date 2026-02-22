"""Serializers for meal plan data."""

from rest_framework import serializers

from .models import MealPlan


class MealPlanListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for the plan list — omits the full plan_data blob."""

    plan_name = serializers.SerializerMethodField()

    class Meta:
        model = MealPlan
        fields = [
            "id",
            "plan_name",
            "plan_type",
            "fitness_goal",
            "calorie_target",
            "created_at",
        ]

    def get_plan_name(self, obj) -> str:
        """Extract plan_name from the JSON blob, falling back to a default."""
        return obj.plan_data.get("plan_name", "Meal Plan")


class MealPlanDetailSerializer(serializers.ModelSerializer):
    """Full serializer including the complete plan_data for the detail view."""

    class Meta:
        model = MealPlan
        fields = [
            "id",
            "user_id",
            "plan_type",
            "fitness_goal",
            "dietary_preferences",
            "calorie_target",
            "protein_target",
            "carbs_target",
            "fat_target",
            "favorite_foods",
            "plan_data",
            "created_at",
        ]
        read_only_fields = fields
