from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    """Endpoint mínimo para validar que o Django sobe corretamente (Sprint 0, tasks.md 2.5)."""

    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"status": "ok", "service": "anki-generator-core"})
