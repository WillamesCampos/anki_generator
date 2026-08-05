"""
Isolamento multi-tenant = isolamento por usuário (ver D3 em
openspec/changes/sprint-1-autenticacao-multi-tenant/design.md — nenhuma
entidade Tenant/Organization separada existe neste projeto).

Qualquer model Django que precise pertencer a um usuário e nunca vazar para
outro (`<ponto_critico id="isolamento-multi-tenant">`) DEVE herdar de
`TenantOwnedModel` em vez de reimplementar o filtro por usuário.
"""

from django.conf import settings
from django.db import models


class TenantOwnedQuerySet(models.QuerySet):
    def for_user(self, user) -> "TenantOwnedQuerySet":
        """Restringe o queryset apenas aos registros pertencentes a `user`."""
        return self.filter(owner=user)


class TenantOwnedManager(models.Manager.from_queryset(TenantOwnedQuerySet)):
    pass


class TenantOwnedModel(models.Model):
    """
    Mixin abstrato: qualquer model que herdar daqui ganha uma FK `owner`
    para o usuário dono do registro, e o `for_user()` reutilizável no
    manager — sem precisar duplicar lógica de filtro em cada view/model.
    """

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="+",
    )

    objects = TenantOwnedManager()

    class Meta:
        abstract = True
