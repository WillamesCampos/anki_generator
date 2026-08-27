"""
Cria o Group `standard_user` (Sprint 5, `permissoes-grupo-sem-contenttype`)
e faz backfill de todo usuário já existente na tabela `User` para dentro
dele — o `post_save` signal (`apps/accounts/signals.py`) só cobre criação
de usuário daqui pra frente; sem esse backfill, qualquer usuário criado
antes desta migration (ex.: ambientes de dev já seedados numa sprint
anterior) ficaria de fora do grupo e perderia acesso às views que passam a
exigi-lo.

Idempotente: `get_or_create` do Group e `add()` no M2M de usuários são
ambos seguros de rodar de novo sem duplicar nada.
"""

from django.db import migrations

from apps.accounts.groups import STANDARD_USER_GROUP


def create_standard_user_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    User = apps.get_model("accounts", "User")

    group, _ = Group.objects.get_or_create(name=STANDARD_USER_GROUP)
    group.user_set.add(*User.objects.all())


def remove_standard_user_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name=STANDARD_USER_GROUP).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(create_standard_user_group, remove_standard_user_group),
    ]
