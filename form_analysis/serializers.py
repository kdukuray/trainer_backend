"""Serializers for form analysis data."""

from rest_framework import serializers

from .models import Exercise, FormAnalysis


class ExerciseSerializer(serializers.ModelSerializer):
    """Serializes exercise definitions for the exercise picker."""

    class Meta:
        model = Exercise
        fields = ["id", "name", "recommended_angle", "instructions"]


class FormAnalysisListSerializer(serializers.ModelSerializer):
    """Compact serializer for the analysis list view."""

    exercise_name = serializers.CharField(source="exercise.name", read_only=True)

    class Meta:
        model = FormAnalysis
        fields = [
            "id",
            "exercise_name",
            "total_reps",
            "good_reps",
            "bad_reps",
            "analyzed_at",
        ]


class FormAnalysisDetailSerializer(serializers.ModelSerializer):
    """Full serializer for the analysis detail view."""

    exercise_name = serializers.CharField(source="exercise.name", read_only=True)
    recommended_angle = serializers.CharField(
        source="exercise.recommended_angle", read_only=True
    )

    class Meta:
        model = FormAnalysis
        fields = [
            "id",
            "user_id",
            "exercise_name",
            "recommended_angle",
            "video_url",
            "total_reps",
            "good_reps",
            "bad_reps",
            "rep_details",
            "load_suggestion",
            "analyzed_at",
        ]
        read_only_fields = fields
