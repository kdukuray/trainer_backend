"""
User profile endpoints.

All views require Supabase JWT authentication. The profile is auto-created on
first access so the frontend never has to issue a separate ``POST /register``.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import UserProfile
from .serializers import UserProfileSerializer


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
