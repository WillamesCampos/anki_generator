"""
Corrige o `Site` (django.contrib.sites, `SITE_ID=1`) que nunca foi
configurado desde o Sprint 0/1 — ficava só com o valor default do Django,
"example.com", literalmente visível no e-mail de recuperação de senha
(Sprint 9): "Olá da example.com!", assunto "[example.com] ...".

`update_or_create` (não `filter().update()`) de propósito: a linha padrão
do `Site` não vem de uma migration do `django.contrib.sites` — vem do
signal `post_migrate` (`create_default_site`, `django/contrib/sites/management.py`),
que só roda **depois** que todas as migrations do comando `migrate`
terminam. Nesse momento (durante a migration), a linha `pk=1` ainda pode
não existir — `filter(pk=1).update(...)` seria um no-op silencioso (não
afeta zero linhas com erro, só não faz nada), e o signal criaria a linha
"example.com" logo em seguida, sobrescrevendo a intenção desta migration.
`update_or_create` garante que a linha já existe com os valores certos
antes do signal rodar — e o signal, ao ver que já existe uma linha, pula a
criação do default (checa `if not Site.objects.exists()`).

`domain` fica em "localhost:8000" por enquanto — não há domínio próprio
ainda (PROMPT_REFINADO.md: compra via Cloudflare "sem pressa"). O
`url_generator` customizado (apps/accounts/serializers.py) não depende
desse campo pra montar o link do reset — só o texto de rodapé do template
do allauth usa. Atualizar pra o domínio real quando ele existir.
"""

from django.db import migrations

OLD_DOMAIN = "example.com"
OLD_NAME = "example.com"
NEW_DOMAIN = "localhost:8000"
NEW_NAME = "Anki Generator"


def set_site_name(apps, schema_editor):
    Site = apps.get_model("sites", "Site")
    Site.objects.update_or_create(
        pk=1, defaults={"domain": NEW_DOMAIN, "name": NEW_NAME}
    )


def revert_site_name(apps, schema_editor):
    Site = apps.get_model("sites", "Site")
    Site.objects.filter(pk=1).update(domain=OLD_DOMAIN, name=OLD_NAME)


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_standard_user_group"),
        ("sites", "0002_alter_domain_unique"),
    ]

    operations = [
        migrations.RunPython(set_site_name, revert_site_name),
    ]
