from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Model de usuário do projeto — reaproveita o `AbstractUser` nativo do
    Django, adicionando `email` como chave única de autenticação
    (`<regra_obrigatoria id="model-usuario">` em PROMPT_REFINADO.md).

    Login acontece via email (Google OAuth já devolve email, não username),
    mas o campo `username` continua existindo por compatibilidade com o
    restante do framework (admin, createsuperuser).
    """

    email = models.EmailField("email address", unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self) -> str:
        return self.email
