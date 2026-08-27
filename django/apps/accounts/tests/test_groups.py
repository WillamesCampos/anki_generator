"""
Atribuição automática do grupo `standard_user` (Sprint 5,
`permissoes-grupo-sem-contenttype`) — via `post_save` signal em `User`
(`apps/accounts/signals.py`), cobre qualquer fluxo de criação (Google,
e-mail/senha, seed via `get_or_create`) sem hook por-view. Ver
openspec/changes/sprint-5-fundacoes-transversais/specs/group-based-authorization/spec.md.
"""

import pytest
from django.contrib.auth.models import Group

from apps.accounts.groups import STANDARD_USER_GROUP
from apps.accounts.models import User


@pytest.mark.django_db
def test_new_user_is_assigned_to_standard_user_group_on_create():
    user = User.objects.create_user(username="new_user", email="new_user@example.com")

    assert user.groups.filter(name=STANDARD_USER_GROUP).exists()


@pytest.mark.django_db
def test_get_or_create_new_user_is_assigned_to_group():
    """Mesmo caminho usado pelo comando de seed (`seed_decks.py`)."""
    user, created = User.objects.get_or_create(
        username="seed_style_user", defaults={"email": "seed_style_user@example.com"}
    )

    assert created
    assert user.groups.filter(name=STANDARD_USER_GROUP).exists()


@pytest.mark.django_db
def test_get_or_create_existing_user_is_not_duplicated_in_group():
    user = User.objects.create_user(username="existing_user", email="existing_user@example.com")
    assert user.groups.filter(name=STANDARD_USER_GROUP).count() == 1

    # Segunda chamada não cria (created=False) — não deve duplicar a
    # associação nem levantar erro no signal (que só roda em created=True).
    same_user, created = User.objects.get_or_create(
        username="existing_user", defaults={"email": "existing_user@example.com"}
    )

    assert not created
    assert same_user.groups.filter(name=STANDARD_USER_GROUP).count() == 1


@pytest.mark.django_db
def test_standard_user_group_creation_is_idempotent():
    group_a, _ = Group.objects.get_or_create(name=STANDARD_USER_GROUP)
    group_b, _ = Group.objects.get_or_create(name=STANDARD_USER_GROUP)

    assert group_a.id == group_b.id
    assert Group.objects.filter(name=STANDARD_USER_GROUP).count() == 1
