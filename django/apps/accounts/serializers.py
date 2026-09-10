"""
Serializer de recuperação de senha (PRD.md §7.1) — personaliza o link do
e-mail enviado pelo dj-rest-auth para apontar para o frontend (SPA). O assunto
e os corpos texto/HTML são overrides nativos do allauth em
`django/templates/account/email/password_reset_key_*`; continuam separados do
serializer para preservar a responsabilidade de cada camada.

Como o `django-allauth` está instalado, `dj-rest-auth` delega o envio pra
`AllAuthPasswordResetForm` (`dj_rest_auth.forms`), não pro
`django.contrib.auth.forms.PasswordResetForm` puro — o que muda onde esse
link é gerado: `AllAuthPasswordResetForm.save()` lê um `url_generator`
opcional dos kwargs (com um default que faz `reverse("password_reset_confirm")`,
uma URL Django clássica que não existe aqui) — é esse `url_generator` que
sobrescrevemos abaixo.

O token (`token` no link) é assinado (HMAC), não criptografado — uma
distinção real: dá pra verificar que ninguém adulterou o valor sem uma
chave secreta, mas o conteúdo (pk do usuário + hash da senha atual +
timestamp) não fica oculto, só íntegro. Gerado por
`allauth.account.forms.default_token_generator`
(`EmailAwarePasswordResetTokenGenerator`, subclasse do
`PasswordResetTokenGenerator` do Django) — invalida sozinho quando a senha
muda (o hash usado na assinatura muda) ou quando o e-mail do usuário muda.
"""

from allauth.account.utils import user_pk_to_url_str
from django.conf import settings
from django.utils.http import urlencode
from dj_rest_auth.serializers import PasswordResetSerializer


def frontend_password_reset_url_generator(request, user, temp_key):
    uid = user_pk_to_url_str(user)
    query = urlencode({"uid": uid, "token": temp_key})
    return f"{settings.FRONTEND_URL}/redefinir-senha?{query}"


class CustomPasswordResetSerializer(PasswordResetSerializer):
    def get_email_options(self):
        return {"url_generator": frontend_password_reset_url_generator}
