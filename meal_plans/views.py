"""
Meal plan endpoints: generate, list, and detail views.

Generation sends user preferences to Gemini and stores the structured JSON.
"""

import json
import logging

from django.conf import settings
from google import genai
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.pagination import CursorPagination
from .models import MealPlan
from .serializers import MealPlanDetailSerializer, MealPlanListSerializer

logger = logging.getLogger(__name__)

MEAL_PLAN_SYSTEM_PROMPT = """You are a sports nutrition AI. Generate a {plan_type} meal plan.

User profile:
- Fitness goal: {fitness_goal}
- Dietary preferences: {dietary_preferences}
- Daily calorie target: {calorie_target} kcal
- Macro targets: Protein {protein_target}g, Carbs {carbs_target}g, Fat {fat_target}g
- Favorite foods to incorporate: {favorite_foods}

Return ONLY valid JSON (no markdown fences) with this exact structure:
{{
  "plan_name": "A descriptive name for this plan",
  "days": [
    {{
      "day": "Monday",
      "meals": [
        {{
          "name": "Pre-Workout Breakfast",
          "timing": "7:00 AM",
          "foods": [
            {{"item": "Oatmeal", "portion": "1 cup cooked", "calories": 150, "protein_g": 5, "carbs_g": 27, "fat_g": 3}}
          ],
          "total_calories": 450
        }}
      ],
      "daily_totals": {{"calories": 2000, "protein_g": 150, "carbs_g": 200, "fat_g": 65}}
    }}
  ],
  "substitutions": [
    {{"original": "Chicken breast", "substitute": "Tofu", "reason": "Plant-based alternative"}}
  ],
  "tips": ["Drink at least 2L of water daily"]
}}

For a daily plan, include exactly 1 day. For a weekly plan, include 7 days (Monday through Sunday).
Ensure the daily totals closely match the user's calorie and macro targets.
Include meal timing suggestions (pre-workout, post-workout, bedtime snack, etc.).
"""


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def generate_meal_plan(request):
    """
    Generate a personalised meal plan using Gemini.

    Parameters:
        request.data: {
            plan_type, fitness_goal, dietary_preferences,
            calorie_target, protein_target, carbs_target, fat_target,
            favorite_foods
        }

    Returns:
        201: The created MealPlan with full plan_data.
        500: If Gemini fails or returns unparseable JSON.
    """
    data = request.data

    plan_type = data.get("plan_type", "daily")
    fitness_goal = data.get("fitness_goal", "maintenance")
    dietary_preferences = data.get("dietary_preferences", [])
    calorie_target = data.get("calorie_target", 2000)
    protein_target = data.get("protein_target", 150)
    carbs_target = data.get("carbs_target", 200)
    fat_target = data.get("fat_target", 65)
    favorite_foods = data.get("favorite_foods", "")

    prompt = MEAL_PLAN_SYSTEM_PROMPT.format(
        plan_type=plan_type,
        fitness_goal=fitness_goal,
        dietary_preferences=", ".join(dietary_preferences) if dietary_preferences else "none",
        calorie_target=calorie_target,
        protein_target=protein_target,
        carbs_target=carbs_target,
        fat_target=fat_target,
        favorite_foods=favorite_foods or "no specific preferences",
    )

    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        raw_text = response.text.strip()

        # Strip markdown code fences if present
        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[1]
        if raw_text.endswith("```"):
            raw_text = raw_text.rsplit("```", 1)[0]
        raw_text = raw_text.strip()

        plan_data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        logger.error("Gemini returned unparseable JSON: %s", exc)
        return Response(
            {"error": "AI generated an invalid response. Please try again."},
            status=500,
        )
    except Exception as exc:
        logger.error("Gemini meal plan generation failed: %s", exc)
        return Response(
            {"error": "Failed to generate meal plan. Please try again."},
            status=500,
        )

    meal_plan = MealPlan.objects.create(
        user_id=request.user.id,
        plan_type=plan_type,
        fitness_goal=fitness_goal,
        dietary_preferences=dietary_preferences,
        calorie_target=calorie_target,
        protein_target=protein_target,
        carbs_target=carbs_target,
        fat_target=fat_target,
        favorite_foods=favorite_foods,
        plan_data=plan_data,
    )

    serializer = MealPlanDetailSerializer(meal_plan)
    return Response(serializer.data, status=201)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_meal_plans(request):
    """
    Return the user's meal plans, newest first, with cursor pagination.

    Query params:
        cursor: ID of the last item from the previous page.
        page_size: Optional page size override (max 50).

    Returns:
        200: { results, next_cursor, has_more }
    """
    queryset = MealPlan.objects.filter(user_id=request.user.id).order_by("-id")
    paginator = CursorPagination()
    page = paginator.paginate_queryset(queryset, request)
    serializer = MealPlanListSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_meal_plan_detail(request, plan_id):
    """
    Return the full detail of a single meal plan.

    Parameters:
        plan_id: Primary key of the MealPlan.

    Returns:
        200: Full MealPlan with plan_data.
        404: If the plan doesn't exist or doesn't belong to this user.
    """
    try:
        meal_plan = MealPlan.objects.get(id=plan_id, user_id=request.user.id)
    except MealPlan.DoesNotExist:
        return Response({"error": "Meal plan not found."}, status=404)

    serializer = MealPlanDetailSerializer(meal_plan)
    return Response(serializer.data)
