"""
Models for exercise form analysis.

Exercise is pre-populated with the 5 supported exercises and their YOLO config.
FormAnalysis records a single video analysis session with per-rep results.
"""

from django.db import models


class Exercise(models.Model):
    """
    A supported exercise with its recommended camera angle and the
    YOLO keypoint/threshold configuration used during analysis.
    """

    name = models.CharField(max_length=100, unique=True)
    recommended_angle = models.CharField(
        max_length=100,
        help_text='E.g. "Side view", "Front view"',
    )
    instructions = models.TextField(
        blank=True,
        default="",
        help_text="Setup and form tips shown to the user before recording",
    )
    metrics_config = models.JSONField(
        default=dict,
        help_text="Keypoints used, threshold values, and metric names",
    )

    def __str__(self) -> str:
        return self.name


class FormAnalysis(models.Model):
    """
    Records one video analysis session for a specific exercise.

    ``rep_details`` is a list of per-rep objects, each containing:
    { "rep": 1, "status": "good"|"bad", "metric_value": 68.5, "feedback": "..." }
    """

    user_id = models.CharField(max_length=255, db_index=True)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)

    video_url = models.URLField(
        max_length=500,
        blank=True,
        default="",
        help_text="Public URL of the uploaded video in Supabase Storage",
    )

    total_reps = models.IntegerField(default=0)
    good_reps = models.IntegerField(default=0)
    bad_reps = models.IntegerField(default=0)

    rep_details = models.JSONField(
        default=list,
        help_text="Per-rep metrics and feedback",
    )
    load_suggestion = models.TextField(
        blank=True,
        default="",
        help_text="AI-generated suggestion for load adjustment based on form quality",
    )

    analyzed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self) -> str:
        return f"{self.exercise.name} — {self.good_reps}/{self.total_reps} good"
