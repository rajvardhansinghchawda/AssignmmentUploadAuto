"""
Auth views: Google OAuth flow, JWT issuance, profile, logout.
Config views: PIEMR credential save/retrieve.
"""
import logging
import requests
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status

from .models import StudentProfile
from .serializers import StudentProfileSerializer, ConfigSerializer
from .authentication import generate_token
from services.crypto import encrypt, decrypt

logger = logging.getLogger(__name__)

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


# ── Google OAuth ──────────────────────────────────────────────────────────────

class GoogleLoginView(APIView):
    """GET /api/auth/google/ — Redirect browser to Google consent screen."""
    permission_classes = [AllowAny]

    def get(self, request):
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": " ".join(settings.GOOGLE_SCOPES),
            "access_type": "offline",
            "prompt": "consent",
        }
        url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
        from django.http import HttpResponseRedirect
        return HttpResponseRedirect(url)


class GoogleCallbackView(APIView):
    """GET /api/auth/google/callback/ — Exchange code for tokens, issue JWT."""
    permission_classes = [AllowAny]

    def get(self, request):
        code = request.query_params.get("code")
        if not code:
            return Response({"error": "Authorization code missing"}, status=400)

        # Exchange code for Google tokens
        token_resp = requests.post(GOOGLE_TOKEN_URL, data={
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        })
        if not token_resp.ok:
            logger.error(f"[auth] Token exchange failed: {token_resp.text}")
            return Response({"error": "Token exchange failed"}, status=400)

        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token", "")
        expires_in = token_data.get("expires_in", 3600)

        # Fetch user info from Google
        userinfo_resp = requests.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if not userinfo_resp.ok:
            return Response({"error": "Failed to fetch user info"}, status=400)

        userinfo = userinfo_resp.json()
        email = userinfo.get("email")
        first_name = userinfo.get("given_name", "")
        last_name = userinfo.get("family_name", "")

        # Get or create Django user
        user, created = User.objects.get_or_create(
            username=email,
            defaults={"email": email, "first_name": first_name, "last_name": last_name},
        )
        if not created:
            user.first_name = first_name
            user.last_name = last_name
            user.save(update_fields=["first_name", "last_name"])

        # Get or create student profile, store encrypted tokens
        expiry = timezone.now() + timezone.timedelta(seconds=expires_in)
        profile, _ = StudentProfile.objects.get_or_create(user=user)
        profile.google_access_token = encrypt(access_token)
        if refresh_token:
            profile.google_refresh_token = encrypt(refresh_token)
        profile.token_expiry = expiry
        profile.save()

        # Issue our own JWT
        jwt_token = generate_token(user)
        is_first_login = not profile.has_piemr_credentials

        from django.http import HttpResponseRedirect
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
        redirect_url = f"{frontend_url}/?token={jwt_token}&new_user={'true' if is_first_login else 'false'}"
        return HttpResponseRedirect(redirect_url)


class LogoutView(APIView):
    """POST /api/auth/logout/ — Client should discard the JWT."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # JWT is stateless; we just confirm logout on the server side.
        # For token blacklisting, a Redis-based blocklist can be added later.
        return Response({"detail": "Logged out successfully."})


class MeView(APIView):
    """GET /api/auth/me/ — Return current user profile."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = request.user.profile
        except StudentProfile.DoesNotExist:
            return Response({"error": "Profile not found"}, status=404)
        return Response(StudentProfileSerializer(profile).data)


# ── Config (PIEMR Credentials) ─────────────────────────────────────────────────

class ConfigView(APIView):
    """GET/POST /api/config/ — Retrieve or save PIEMR portal credentials."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = request.user.profile
        except StudentProfile.DoesNotExist:
            return Response({})
        return Response({
            "enrollment_no": profile.enrollment_no,
            "has_password": bool(profile.piemr_password),
            "is_setup_complete": profile.is_setup_complete,
        })

    def post(self, request):
        serializer = ConfigSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        profile, _ = StudentProfile.objects.get_or_create(user=request.user)
        profile.enrollment_no = serializer.validated_data["enrollment_no"]
        profile.piemr_password = encrypt(serializer.validated_data["piemr_password"])
        profile.is_setup_complete = True
        profile.save()

        logger.info(f"[config] Credentials saved for user {request.user.email}")
        return Response({"detail": "Credentials saved securely."}, status=200)
