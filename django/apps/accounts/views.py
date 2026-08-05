import os

from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from rest_framework import exceptions
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from .tokens import is_refresh_token_revoked, revoke_refresh_token


class GoogleLoginView(SocialLoginView):
    """
    Endpoint REST de login social (D2 em design.md): a SPA já fez o
    consentimento com o Google do lado dela e manda pra cá o access_token
    obtido — esta view usa o `GoogleOAuth2Adapter` do allauth pra validar
    esse token junto ao Google e, se válido, devolve o JWT emitido pelo
    simplejwt (via `dj-rest-auth`, configurado com `USE_JWT=True`).
    """

    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client
    callback_url = os.environ.get(
        "GOOGLE_OAUTH_CALLBACK_URL", "http://localhost:8000/api/v1/auth/google/callback/"
    )


class BlocklistAwareTokenRefreshSerializer(TokenRefreshSerializer):
    """Recusa refresh tokens já revogados (ver apps/accounts/tokens.py)."""

    def validate(self, attrs):
        refresh = RefreshToken(attrs["refresh"])
        if is_refresh_token_revoked(refresh["jti"]):
            raise exceptions.AuthenticationFailed("Refresh token has been revoked.")
        return super().validate(attrs)


class TokenRefreshWithBlocklistView(TokenRefreshView):
    serializer_class = BlocklistAwareTokenRefreshSerializer


class LogoutView(APIView):
    """Revoga o refresh token no Redis — logout tem efeito imediato, não espera a expiração."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh = request.data.get("refresh")
        if not refresh:
            return Response({"detail": "refresh is required."}, status=400)

        revoke_refresh_token(refresh)
        return Response({"detail": "Logged out."}, status=200)
