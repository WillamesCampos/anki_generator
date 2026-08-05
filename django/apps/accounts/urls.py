from django.urls import path

from .views import GoogleLoginView, LogoutView, TokenRefreshWithBlocklistView

app_name = "accounts"

urlpatterns = [
    path("google/", GoogleLoginView.as_view(), name="google-login"),
    path("token/refresh/", TokenRefreshWithBlocklistView.as_view(), name="token-refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
]
