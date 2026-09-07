"""
`<ponto_critico id="isolamento-multi-tenant">`: falha de isolamento entre
tenants é crítica/bloqueante. Estes testes validam o mixin `TenantOwnedModel`
que qualquer model futuro (Sprint 2 em diante) DEVE reutilizar.
"""

import pytest

from apps.accounts.models import User
from apps.accounts.tests.conftest import Widget


@pytest.mark.django_db(transaction=True)
def test_for_user_returns_only_owned_records(widget_table):
    owner_a = User.objects.create_user(username="owner_a", email="owner_a@example.com")
    owner_b = User.objects.create_user(username="owner_b", email="owner_b@example.com")

    Widget.objects.create(owner=owner_a, name="a-widget")
    Widget.objects.create(owner=owner_b, name="b-widget")

    assert list(Widget.objects.for_user(owner_a).values_list("name", flat=True)) == [
        "a-widget"
    ]
    assert list(Widget.objects.for_user(owner_b).values_list("name", flat=True)) == [
        "b-widget"
    ]


@pytest.mark.django_db(transaction=True)
def test_cross_tenant_access_by_id_is_blocked(widget_table):
    owner_a = User.objects.create_user(username="owner_c", email="owner_c@example.com")
    owner_b = User.objects.create_user(username="owner_d", email="owner_d@example.com")

    widget = Widget.objects.create(owner=owner_a, name="secret")

    # O ponto crítico em si: owner_b NUNCA pode enxergar o registro de owner_a,
    # nem sabendo o ID exato.
    assert not Widget.objects.for_user(owner_b).filter(pk=widget.pk).exists()
    assert Widget.objects.for_user(owner_a).filter(pk=widget.pk).exists()
