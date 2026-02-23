"""
Supabase JWT authentication backend for Django REST Framework.

Verifies access tokens from the Authorization header using the project's
JWKS endpoint (for ES256 / ECC P-256 keys) with a fallback to the legacy
HS256 shared secret. Attaches a lightweight ``SupabaseUser`` to
``request.user`` on success.
"""

import logging

import jwt
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

logger = logging.getLogger(__name__)

_jwks_client: jwt.PyJWKClient | None = None


def _get_jwks_client() -> jwt.PyJWKClient:
    """
    Lazily initialise and return a cached PyJWKClient for the Supabase JWKS
    endpoint. The client caches keys internally (default 5 min lifespan).
    """
    global _jwks_client
    if _jwks_client is None:
        jwks_url = f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
        _jwks_client = jwt.PyJWKClient(jwks_url, cache_keys=True, lifespan=300)
    return _jwks_client


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
    Resolves the signing key from the project's JWKS endpoint, falling back
    to the ``SUPABASE_JWT_SECRET`` for legacy HS256 tokens.
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

        try:
            signing_key, algorithms = self._resolve_signing_key(token)
            payload = jwt.decode(
                token,
                signing_key,
                algorithms=algorithms,
                audience="authenticated",
            )
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Token has expired.")
        except jwt.InvalidTokenError as exc:
            logger.error("JWT verification failed: %s", exc)
            raise AuthenticationFailed(f"Invalid token: {exc}")

        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationFailed("Token missing 'sub' claim.")

        email = payload.get("email", "")
        user = SupabaseUser(uid=user_id, email=email)

        return (user, payload)

    def _resolve_signing_key(self, token: str):
        """
        Determine the correct key and algorithm(s) for verifying *token*.

        Tries the JWKS endpoint first (handles ES256 / ECC keys). Falls back
        to the legacy ``SUPABASE_JWT_SECRET`` for HS256 tokens when JWKS
        lookup fails (e.g. token has no ``kid`` header).

        Returns:
            Tuple of (key, algorithm_list).
        """
        header = jwt.get_unverified_header(token)
        alg = header.get("alg", "")

        if header.get("kid") and settings.SUPABASE_URL:
            try:
                jwk = _get_jwks_client().get_signing_key_from_jwt(token)
                return jwk.key, [alg]
            except jwt.PyJWKClientError as exc:
                logger.warning("JWKS key lookup failed, trying legacy secret: %s", exc)

        if not settings.SUPABASE_JWT_SECRET:
            raise AuthenticationFailed(
                "JWT verification failed: no JWKS key found and no legacy secret configured."
            )

        return settings.SUPABASE_JWT_SECRET, ["HS256", "HS384", "HS512"]
