from dj_rest_auth.views import LoginView
from django.urls import path

from .views import GoogleLoginView, LogoutView, TokenRefreshWithBlocklistView

app_name = "accounts"

urlpatterns = [
    # Login por e-mail/senha (dj-rest-auth padrão — User.USERNAME_FIELD já é
    # "email", então LoginSerializer autentica por e-mail sem configuração
    # extra). Só o login: cadastro e vínculo com conta Google ficam no
    # backlog de refinamento (PRD.md, seção 7.1) até as decisões de
    # segurança (verificação de e-mail, EMAIL_BACKEND) serem tomadas.
    path("login/", LoginView.as_view(), name="login"),
    path("google/", GoogleLoginView.as_view(), name="google-login"),
    path("token/refresh/", TokenRefreshWithBlocklistView.as_view(), name="token-refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
]
