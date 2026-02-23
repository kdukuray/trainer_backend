"""
Calorie tracking endpoints: analyze a food photo, list logs, and get detail.

The analyze endpoint sends the image to Gemini for structured nutritional
estimation, then optionally uploads it to Supabase Storage.
"""

import base64
import json
import logging
import uuid

from django.conf import settings
from google import genai
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.pagination import CursorPagination
from .models import MealLog
from .serializers import MealLogDetailSerializer, MealLogListSerializer

logger = logging.getLogger(__name__)

CALORIE_SYSTEM_PROMPT = """You are a nutrition analysis AI. Analyze the food in this image.
Identify each food item, estimate portion sizes, and provide a structured response.

Return ONLY valid JSON (no markdown fences) with this exact structure:
{
  "food_name": "A concise name for the meal",
  "description": "Brief description of what you see",
  "calories": 550,
  "protein_g": 35.0,
  "carbs_g": 45.0,
  "fat_g": 18.0,
  "fiber_g": 6.0,
  "serving_size": "1 plate, approximately 400g",
  "nutritional_details": {
    "sodium_mg": 800,
    "sugar_g": 8.0,
    "saturated_fat_g": 5.0,
    "cholesterol_mg": 75,
    "vitamin_a_pct": 15,
    "vitamin_c_pct": 20,
    "calcium_pct": 10,
    "iron_pct": 25
  }
}

Be as accurate as possible. If you cannot identify the food, make your best estimate.
All numeric values should be numbers (not strings). Calories should be an integer.
"""


def _upload_image_to_supabase(image_file) -> str:
    """
    Upload an image file to Supabase Storage and return its public URL.

    Parameters:
        image_file: A Django UploadedFile instance.

    Returns:
        The public URL string, or empty string if upload fails.
    """
    try:
        from supabase import create_client

        client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
        file_ext = image_file.name.split(".")[-1] if "." in image_file.name else "jpg"
        file_path = f"meal-photos/{uuid.uuid4()}.{file_ext}"
        file_bytes = image_file.read()
        image_file.seek(0)  # Reset for potential re-read

        client.storage.from_("trainr-uploads").upload(
            file_path,
            file_bytes,
            {"content-type": image_file.content_type or "image/jpeg"},
        )
        public_url = client.storage.from_("trainr-uploads").get_public_url(file_path)
        return public_url
    except Exception as exc:
        logger.warning("Supabase image upload failed (non-fatal): %s", exc)
        return ""


@api_view(["POST"])
@parser_classes([MultiPartParser])
@permission_classes([IsAuthenticated])
def analyze_meal_image(request):
    """
    Receive a meal photo, analyze it with Gemini, and save a MealLog.

    Parameters:
        request.FILES['image']: The meal photo.

    Returns:
        201: Created MealLog with full nutritional breakdown.
        400: If no image is provided.
        500: If Gemini fails.
    """
    image_file = request.FILES.get("image")
    if not image_file:
        return Response({"error": "No image provided."}, status=400)

    # Upload to Supabase Storage (best-effort, won't block on failure)
    image_url = _upload_image_to_supabase(image_file)

    # Send to Gemini for analysis
    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        image_bytes = image_file.read()
        image_file.seek(0)
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        content_type = image_file.content_type or "image/jpeg"
        image_part = genai.types.Part.from_bytes(data=image_bytes, mime_type=content_type)

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[CALORIE_SYSTEM_PROMPT, image_part],
        )
        raw_text = response.text.strip()

        # Strip markdown code fences if present
        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[1]
        if raw_text.endswith("```"):
            raw_text = raw_text.rsplit("```", 1)[0]
        raw_text = raw_text.strip()

        analysis = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        logger.error("Gemini returned unparseable JSON for calorie analysis: %s", exc)
        return Response(
            {"error": "AI generated an invalid response. Please try again."},
            status=500,
        )
    except Exception as exc:
        logger.error("Gemini calorie analysis failed: %s", exc)
        return Response(
            {"error": "Failed to analyze the image. Please try again."},
            status=500,
        )

    meal_log = MealLog.objects.create(
        user_id=request.user.id,
        food_name=analysis.get("food_name", "Unknown Food"),
        description=analysis.get("description", ""),
        calories=int(analysis.get("calories", 0)),
        protein_g=float(analysis.get("protein_g", 0)),
        carbs_g=float(analysis.get("carbs_g", 0)),
        fat_g=float(analysis.get("fat_g", 0)),
        fiber_g=float(analysis.get("fiber_g", 0)),
        serving_size=analysis.get("serving_size", ""),
        nutritional_details=analysis.get("nutritional_details", {}),
        image_url=image_url,
    )

    serializer = MealLogDetailSerializer(meal_log)
    return Response(serializer.data, status=201)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_meal_logs(request):
    """
    Return the user's meal logs, newest first, with cursor pagination.

    Query params:
        cursor: ID of the last item from the previous page.

    Returns:
        200: { results, next_cursor, has_more }
    """
    queryset = MealLog.objects.filter(user_id=request.user.id).order_by("-id")
    paginator = CursorPagination()
    page = paginator.paginate_queryset(queryset, request)
    serializer = MealLogListSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_meal_log_detail(request, log_id):
    """
    Return full detail of a single meal log.

    Parameters:
        log_id: Primary key of the MealLog.

    Returns:
        200: Full MealLog with all nutritional data.
        404: If the log doesn't exist or doesn't belong to this user.
    """
    try:
        meal_log = MealLog.objects.get(id=log_id, user_id=request.user.id)
    except MealLog.DoesNotExist:
        return Response({"error": "Meal log not found."}, status=404)

    serializer = MealLogDetailSerializer(meal_log)
    return Response(serializer.data)
