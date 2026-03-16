"""Serializers for the UserProfile model."""

from rest_framework import serializers

from .models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializes every editable field on UserProfile.

    ``user_id`` is read-only — it is set from the JWT, never by the client.
    """

    class Meta:
        model = UserProfile
        fields = [
            "user_id",
            "display_name",
            "email",
            "fitness_goal",
            "dietary_preferences",
            "current_body_type",
            "goal_body_type",
            "weight",
            "height",
            "timeline",
            "knowledge_rank",
            "calorie_target",
            "protein_target",
            "carbs_target",
            "fat_target",
            "recommended_daily_calories",
            "recommended_weekly_workouts",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "user_id",
            "recommended_daily_calories",
            "recommended_weekly_workouts",
            "created_at",
            "updated_at",
        ]
