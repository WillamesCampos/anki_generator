"""
Autorização de decks/cards/categories/reviews (Sprint 5,
`permissoes-grupo-sem-contenttype`).

`Deck`/`Card`/`Category`/`CardReview` não são `models.Model` — sem
`ContentType`, `Permission` automático do Django não se aplica a elas (ver
D2 em openspec/changes/sprint-5-fundacoes-transversais/design.md). A
autorização aqui é por `Group` (rótulo grosso de capacidade), não por
`Permission` granular por ação: qualquer usuário autenticado pertencente a
`AUTHORIZED_GROUPS` pode acessar essas views, sujeito ao isolamento por
`owner_id` já existente em cada repositório/view. Desenhado para aceitar um
grupo `ai_agent` (Sprint 10) só adicionando o nome a `AUTHORIZED_GROUPS`,
sem mudar o mecanismo.
"""

from rest_framework.permissions import BasePermission

from apps.accounts.groups import STANDARD_USER_GROUP

AUTHORIZED_GROUPS = {STANDARD_USER_GROUP}


class HasAuthorizedGroup(BasePermission):
    """Nega acesso a usuários autenticados sem grupo autorizado (distinto de 401)."""

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False

        return user.groups.filter(name__in=AUTHORIZED_GROUPS).exists()
