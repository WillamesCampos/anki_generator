from dj_rest_auth.views import LoginView, PasswordResetConfirmView, PasswordResetView
from django.urls import path

from .views import GoogleLoginView, LogoutView, TokenRefreshWithBlocklistView

app_name = "accounts"

urlpatterns = [
    # Login por e-mail/senha (dj-rest-auth padrão — User.USERNAME_FIELD já é
    # "email", então LoginSerializer autentica por e-mail sem configuração
    # extra). Cadastro e vínculo com conta Google ficam no backlog de
    # refinamento (PRD.md, seção 7.1).
    path("login/", LoginView.as_view(), name="login"),
    path("google/", GoogleLoginView.as_view(), name="google-login"),
    path(
        "token/refresh/", TokenRefreshWithBlocklistView.as_view(), name="token-refresh"
    ),
    path("logout/", LogoutView.as_view(), name="logout"),
    # Recuperação de senha (PRD.md §7.1): `password/reset/` recebe o e-mail
    # e dispara o envio (sempre 200, mesmo pra e-mail inexistente — não
    # revela se a conta existe); `password/reset/confirm/` recebe
    # `uid`/`token` (do link do e-mail) + a nova senha.
    path("password/reset/", PasswordResetView.as_view(), name="password-reset"),
    path(
        "password/reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
]
