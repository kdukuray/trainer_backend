"""
Management command to populate the database with the 5 supported exercises.

Usage:
    uv run python manage.py seed_exercises
"""

from django.core.management.base import BaseCommand

from form_analysis.models import Exercise

EXERCISES = [
    {
        "name": "Push-ups",
        "recommended_angle": "Front view",
        "instructions": (
            "Place your camera on the ground facing you from the front. "
            "Ensure your full body is visible from head to toe. "
            "Perform push-ups with a controlled tempo — aim for 2 seconds down, 1 second up. "
            "Keep your body in a straight line from head to heels."
        ),
        "metrics_config": {
            "keypoints": ["shoulders", "elbows", "hips"],
            "metric": "elbow_flare_angle",
            "threshold": 75,
            "unit": "degrees",
            "description": "Angle at shoulder between hip-shoulder-elbow. Above 75° indicates excessive elbow flare.",
        },
    },
    {
        "name": "Pull-ups",
        "recommended_angle": "Front view",
        "instructions": (
            "Set your camera at arm's length in front of you, capturing from waist to above the bar. "
            "Ensure the bar and your head are visible throughout the movement. "
            "Start from a dead hang and pull until your chin clears the bar."
        ),
        "metrics_config": {
            "keypoints": ["nose", "shoulders", "elbows", "hips"],
            "metric": "chin_above_bar",
            "description": "Checks if the nose Y-coordinate goes above the average shoulder Y-coordinate during the up phase.",
        },
    },
    {
        "name": "Bench Press",
        "recommended_angle": "Side view",
        "instructions": (
            "Place your camera to one side at bench height, capturing your full torso and arms. "
            "Ensure the bar path is visible from lockout to chest. "
            "Use a controlled tempo and full range of motion."
        ),
        "metrics_config": {
            "keypoints": ["shoulders", "elbows", "wrists", "hips"],
            "metric": "elbow_angle_at_bottom",
            "good_range": [80, 100],
            "lockout_angle": 160,
            "unit": "degrees",
            "description": "Elbow angle at the bottom should be 80-100°. Full lockout (>160°) required at top.",
        },
    },
    {
        "name": "Curls",
        "recommended_angle": "Side view",
        "instructions": (
            "Position your camera to one side, capturing your full arm from shoulder to wrist. "
            "Stand upright and keep your elbows pinned to your sides. "
            "Perform full range of motion — fully extend and fully contract."
        ),
        "metrics_config": {
            "keypoints": ["shoulders", "elbows", "wrists", "hips"],
            "metric": "range_of_motion",
            "min_rom": 80,
            "unit": "degrees",
            "description": "Elbow angle range of motion should be at least 80°. Upper arm should stay stable (low std deviation).",
        },
    },
    {
        "name": "Crunches",
        "recommended_angle": "Side view",
        "instructions": (
            "Lie on your back and place the camera to one side at floor level. "
            "Ensure your head, shoulders, and hips are visible. "
            "Perform controlled crunches — lift shoulders, don't pull your neck."
        ),
        "metrics_config": {
            "keypoints": ["nose", "shoulders", "hips", "knees"],
            "metric": "trunk_lift_angle",
            "good_range": [20, 55],
            "unit": "degrees",
            "description": "Trunk angle from horizontal should be 20-55°. Too little = insufficient lift. Too much = sit-up, not crunch.",
        },
    },
]


class Command(BaseCommand):
    help = "Seed the database with the 5 supported exercises and their YOLO configurations."

    def handle(self, *args, **options):
        """Insert or update all exercises."""
        created_count = 0
        for ex_data in EXERCISES:
            _, created = Exercise.objects.update_or_create(
                name=ex_data["name"],
                defaults={
                    "recommended_angle": ex_data["recommended_angle"],
                    "instructions": ex_data["instructions"],
                    "metrics_config": ex_data["metrics_config"],
                },
            )
            if created:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(EXERCISES)} exercises ({created_count} new)."
            )
        )
