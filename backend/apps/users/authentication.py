"""
Custom JWT authentication for DRF.
Tokens are issued after Google OAuth callback and stored client-side.
"""
import jwt
import logging
from datetime import datetime, timezone
from django.conf import settings
from django.contrib.auth.models import User
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

logger = logging.getLogger(__name__)


def generate_token(user: User) -> str:
    """Generate a signed JWT for the given user."""
    from datetime import timedelta
    expiry = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRY_HOURS)
    payload = {
        "user_id": user.id,
        "email": user.email,
        "exp": expiry,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")


def decode_token(token: str) -> dict:
    """Decode and validate a JWT. Raises AuthenticationFailed on error."""
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise AuthenticationFailed("Token has expired. Please log in again.")
    except jwt.InvalidTokenError as exc:
        raise AuthenticationFailed(f"Invalid token: {exc}")


class JWTAuthentication(BaseAuthentication):
    """DRF authentication class that reads Bearer token from Authorization header."""

    def authenticate(self, request):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None  # Let other authenticators try

        token = auth_header.split(" ", 1)[1].strip()
        payload = decode_token(token)

        try:
            user = User.objects.get(id=payload["user_id"])
        except User.DoesNotExist:
            raise AuthenticationFailed("User not found.")

        return (user, token)

    def authenticate_header(self, request):
        return "Bearer"
