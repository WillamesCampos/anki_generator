"""
`_Widget` é um model de teste descartável (criado/destruído só durante os
testes via `schema_editor`, nunca migrado de verdade) usado para validar os
mixins abstratos `TenantOwnedModel` e `AuditMixin` com um caso concreto —
já que nenhum model de produto real os usa ainda (isso só acontece a partir
da Sprint 2).
"""

import pytest
from django.db import connection, models

from apps.accounts.audit import AuditMixin
from apps.accounts.tenancy import TenantOwnedModel


class Widget(AuditMixin, TenantOwnedModel):
    name = models.CharField(max_length=100)

    class Meta:
        app_label = "accounts"


@pytest.fixture
def widget_table(django_db_blocker):
    with django_db_blocker.unblock():
        with connection.schema_editor() as editor:
            editor.create_model(Widget)
        yield
        with connection.schema_editor() as editor:
            editor.delete_model(Widget)


@pytest.fixture(autouse=True)
def _clear_cache():
    """Evita que o throttle de um teste vaze pro próximo (cache Redis compartilhado)."""
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()
