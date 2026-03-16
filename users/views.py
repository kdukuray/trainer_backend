"""
User profile endpoints.

All views require Supabase JWT authentication. The profile is auto-created on
first access so the frontend never has to issue a separate ``POST /register``.
"""

import json
import logging

from django.conf import settings
from google import genai
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import UserProfile
from .serializers import UserProfileSerializer

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_profile(request):
    """
    Return the authenticated user's profile, creating it if it doesn't exist.

    Returns:
        200: Serialized UserProfile.
    """
    profile, _created = UserProfile.objects.get_or_create(
        user_id=request.user.id,
        defaults={"email": request.user.email},
    )
    serializer = UserProfileSerializer(profile)
    return Response(serializer.data)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """
    Update the authenticated user's profile with the provided fields.

    Parameters:
        request.data: Partial or full UserProfile fields to update.

    Returns:
        200: Updated serialized UserProfile.
        400: Validation errors.
    """
    profile, _created = UserProfile.objects.get_or_create(
        user_id=request.user.id,
        defaults={"email": request.user.email},
    )
    serializer = UserProfileSerializer(profile, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


RECOMMENDATION_PROMPT = """You are a certified fitness and nutrition advisor.
Based on the following user profile, determine two things:
1. How many calories they should consume per day.
2. How many times per week they should work out.

User profile:
- Weight: {weight} lbs
- Height: {height} inches
- Fitness goal: {fitness_goal}
- Current body type: {current_body_type}
- Goal body type: {goal_body_type}
- Timeline to reach goal: {timeline}

Return ONLY valid JSON (no markdown fences) with exactly this structure:
{{"daily_calories": <integer>, "weekly_workouts": <integer>}}

Be realistic and evidence-based. Consider their body type transition, goal, and
timeline when calculating. The weekly_workouts value should be between 2 and 7.
"""


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def generate_recommendations(request):
    """
    Use Gemini to generate personalised calorie and workout recommendations.

    Reads the user's profile (weight, height, timeline, fitness_goal,
    current_body_type, goal_body_type) and returns AI-generated values that
    are also persisted on the profile.

    Returns:
        200: {"daily_calories": int, "weekly_workouts": int}
        400: If required profile fields are missing.
        500: If Gemini fails or returns unparseable JSON.
    """
    profile, _created = UserProfile.objects.get_or_create(
        user_id=request.user.id,
        defaults={"email": request.user.email},
    )

    missing = []
    if not profile.weight:
        missing.append("weight")
    if not profile.height:
        missing.append("height")
    if not profile.timeline:
        missing.append("timeline")
    if not profile.fitness_goal:
        missing.append("fitness_goal")
    if not profile.current_body_type:
        missing.append("current_body_type")
    if not profile.goal_body_type:
        missing.append("goal_body_type")

    if missing:
        return Response(
            {"error": f"Please fill in: {', '.join(missing)}"},
            status=400,
        )

    timeline_display = dict(UserProfile.Timeline.choices).get(
        profile.timeline, profile.timeline,
    )

    prompt = RECOMMENDATION_PROMPT.format(
        weight=profile.weight,
        height=profile.height,
        fitness_goal=profile.fitness_goal,
        current_body_type=profile.current_body_type,
        goal_body_type=profile.goal_body_type,
        timeline=timeline_display,
    )

    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        raw_text = response.text.strip()

        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[1]
        if raw_text.endswith("```"):
            raw_text = raw_text.rsplit("```", 1)[0]
        raw_text = raw_text.strip()

        result = json.loads(raw_text)
        daily_calories = int(result["daily_calories"])
        weekly_workouts = int(result["weekly_workouts"])
    except json.JSONDecodeError as exc:
        logger.error("Gemini returned unparseable JSON for recommendations: %s", exc)
        return Response(
            {"error": "AI generated an invalid response. Please try again."},
            status=500,
        )
    except Exception as exc:
        logger.error("Gemini recommendation generation failed: %s", exc)
        return Response(
            {"error": "Failed to generate recommendations. Please try again."},
            status=500,
        )

    profile.recommended_daily_calories = daily_calories
    profile.recommended_weekly_workouts = weekly_workouts
    profile.save(update_fields=["recommended_daily_calories", "recommended_weekly_workouts"])

    return Response({
        "daily_calories": daily_calories,
        "weekly_workouts": weekly_workouts,
    })
