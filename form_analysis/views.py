"""
Form analysis endpoints: list exercises, upload videos, and view results.

The analyze endpoint saves the video to a temp file, runs YOLO analysis,
optionally uploads to Supabase Storage, and persists the results.
"""

import logging
import os
import tempfile
import uuid

from django.conf import settings
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.pagination import CursorPagination
from .analyzer import analyze_video, generate_load_suggestion
from .models import Exercise, FormAnalysis
from .serializers import (
    ExerciseSerializer,
    FormAnalysisDetailSerializer,
    FormAnalysisListSerializer,
)

logger = logging.getLogger(__name__)


def _upload_video_to_supabase(video_file) -> str:
    """
    Upload a video file to Supabase Storage and return its public URL.

    Parameters:
        video_file: A Django UploadedFile instance.

    Returns:
        The public URL string, or empty string if upload fails.
    """
    try:
        from supabase import create_client

        client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
        file_ext = video_file.name.split(".")[-1] if "." in video_file.name else "mp4"
        file_path = f"form-videos/{uuid.uuid4()}.{file_ext}"
        file_bytes = video_file.read()
        video_file.seek(0)

        client.storage.from_("trainr-uploads").upload(
            file_path,
            file_bytes,
            {"content-type": video_file.content_type or "video/mp4"},
        )
        return client.storage.from_("trainr-uploads").get_public_url(file_path)
    except Exception as exc:
        logger.warning("Supabase video upload failed (non-fatal): %s", exc)
        return ""


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_exercises(request):
    """
    Return all available exercises with their recommended angles and instructions.

    Returns:
        200: List of Exercise objects.
    """
    exercises = Exercise.objects.all().order_by("name")
    serializer = ExerciseSerializer(exercises, many=True)
    return Response(serializer.data)


@api_view(["POST"])
@parser_classes([MultiPartParser])
@permission_classes([IsAuthenticated])
def analyze_form(request):
    """
    Upload an exercise video, analyse it with YOLO, and save the results.

    Parameters:
        request.data['exercise_id']: PK of the Exercise to analyse.
        request.FILES['video']: The exercise video.

    Returns:
        201: Created FormAnalysis with rep details and load suggestion.
        400: If exercise_id or video is missing.
        404: If the exercise doesn't exist.
        500: If YOLO analysis fails.
    """
    exercise_id = request.data.get("exercise_id")
    video_file = request.FILES.get("video")

    if not exercise_id:
        return Response({"error": "exercise_id is required."}, status=400)
    if not video_file:
        return Response({"error": "No video file provided."}, status=400)

    try:
        exercise = Exercise.objects.get(id=exercise_id)
    except Exercise.DoesNotExist:
        return Response({"error": "Exercise not found."}, status=404)

    # Upload to Supabase Storage (best-effort)
    video_url = _upload_video_to_supabase(video_file)

    # Write to temp file for OpenCV processing
    suffix = os.path.splitext(video_file.name)[1] or ".mp4"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        for chunk in video_file.chunks():
            tmp.write(chunk)
        tmp.close()

        result = analyze_video(exercise.name, tmp.name)
    except Exception as exc:
        logger.error("Form analysis failed for %s: %s", exercise.name, exc)
        return Response(
            {"error": "Video analysis failed. Please try a different video."},
            status=500,
        )
    finally:
        os.unlink(tmp.name)

    load_suggestion = generate_load_suggestion(
        exercise.name, result["good_reps"], result["total_reps"]
    )

    analysis = FormAnalysis.objects.create(
        user_id=request.user.id,
        exercise=exercise,
        video_url=video_url,
        total_reps=result["total_reps"],
        good_reps=result["good_reps"],
        bad_reps=result["bad_reps"],
        rep_details=result["rep_details"],
        load_suggestion=load_suggestion,
    )

    serializer = FormAnalysisDetailSerializer(analysis)
    return Response(serializer.data, status=201)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_analyses(request):
    """
    Return the user's past form analyses, newest first, with cursor pagination.

    Query params:
        cursor: ID of the last item from the previous page.

    Returns:
        200: { results, next_cursor, has_more }
    """
    queryset = FormAnalysis.objects.filter(user_id=request.user.id).order_by("-id")
    paginator = CursorPagination()
    page = paginator.paginate_queryset(queryset, request)
    serializer = FormAnalysisListSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_analysis_detail(request, analysis_id):
    """
    Return full detail of a single form analysis.

    Parameters:
        analysis_id: Primary key of the FormAnalysis.

    Returns:
        200: Full FormAnalysis with rep details and load suggestion.
        404: If the analysis doesn't exist or doesn't belong to this user.
    """
    try:
        analysis = FormAnalysis.objects.get(id=analysis_id, user_id=request.user.id)
    except FormAnalysis.DoesNotExist:
        return Response({"error": "Analysis not found."}, status=404)

    serializer = FormAnalysisDetailSerializer(analysis)
    return Response(serializer.data)
