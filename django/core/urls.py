"""
URLs raiz do projeto.

`<regra_obrigatoria id="versionamento-url">`: todas as rotas de API DEVEM ser
versionadas (`/api/v1/...`).
"""

from django.contrib import admin
from django.urls import include, path

from .views import HealthCheckView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/health/", HealthCheckView.as_view(), name="health"),
    path("api/v1/auth/", include("apps.accounts.urls")),
]
