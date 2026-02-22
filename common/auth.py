"""
Supabase JWT authentication backend for Django REST Framework.

Decodes the access token from the Authorization header using the project's
JWT secret, then looks up (or auto-creates) a UserProfile row so every
authenticated request has ``request.user`` set to a lightweight user object.
"""

import jwt
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


class SupabaseUser:
    """
    Minimal user-like object attached to ``request.user``.

    Attributes:
        id: The Supabase auth UUID.
        email: Email address from the JWT claims.
    """

    def __init__(self, uid: str, email: str = ""):
        self.id = uid
        self.email = email

    @property
    def is_authenticated(self) -> bool:
        """Always True — this object only exists after successful verification."""
        return True

    def __str__(self) -> str:
        return self.email or self.id


class SupabaseJWTAuthentication(BaseAuthentication):
    """
    Authenticate incoming requests by verifying Supabase-issued JWTs.

    Expects the header: ``Authorization: Bearer <access_token>``
    Validates using the ``SUPABASE_JWT_SECRET`` from settings.
    Returns a ``(SupabaseUser, token)`` tuple on success.
    """

    keyword = "Bearer"

    def authenticate(self, request):
        """
        Decode and verify the JWT from the Authorization header.

        Parameters:
            request: DRF Request object.

        Returns:
            Tuple of (SupabaseUser, decoded_token) or None if no header.

        Raises:
            AuthenticationFailed: If the token is expired, invalid, or missing
                                  the required ``sub`` claim.
        """
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith(f"{self.keyword} "):
            return None

        token = auth_header[len(self.keyword) + 1 :]

        if not settings.SUPABASE_JWT_SECRET:
            raise AuthenticationFailed("Server JWT secret is not configured.")

        try:
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience="authenticated",
            )
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Token has expired.")
        except jwt.InvalidTokenError as exc:
            raise AuthenticationFailed(f"Invalid token: {exc}")

        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationFailed("Token missing 'sub' claim.")

        email = payload.get("email", "")
        user = SupabaseUser(uid=user_id, email=email)

        return (user, payload)
