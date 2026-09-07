"""
`<regra_obrigatoria id="permissoes-django">`: autorização construída sobre os
models nativos `Permission`/`Group`, sem sistema paralelo. Como o
`AUTH_USER_MODEL` foi customizado nesta sprint, este teste confirma que o
mecanismo nativo continua funcionando normalmente com o novo model de
usuário — não é um requisito novo, é a garantia de que a troca de model não
quebrou o que o Django já oferece.
"""

import pytest
from django.contrib.auth.models import Group, Permission

from apps.accounts.models import User


@pytest.mark.django_db
def test_permission_via_group_works_with_custom_user():
    user = User.objects.create_user(username="perm_user", email="perm_user@example.com")
    group = Group.objects.create(name="editors")
    permission = Permission.objects.get(codename="add_group")
    group.permissions.add(permission)
    user.groups.add(group)

    assert user.has_perm("auth.add_group")


@pytest.mark.django_db
def test_user_without_permission_is_denied():
    user = User.objects.create_user(
        username="no_perm_user", email="no_perm_user@example.com"
    )

    assert not user.has_perm("auth.add_group")
