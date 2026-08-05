"""
Model/mixin de auditoria (`<regra_obrigatoria id="auditoria">` em
PROMPT_REFINADO.md): `created_at`/`created_by`/`updated_at`/`updated_by`,
opcionais no banco, mas preenchidos automaticamente pelos serializers a
partir da request autenticada — nunca aceitos como input do cliente.
"""

from django.conf import settings
from django.db import models
from rest_framework import serializers


class AuditMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    class Meta:
        abstract = True


class AuditSerializerMixin(serializers.Serializer):
    """
    Ambos os campos são `read_only`: o DRF nunca aceita `created_by`/
    `updated_by` vindos do cliente, em nenhuma operação — não depende de
    `pop()` manual, é a própria validação do framework que garante isso.

    NÃO usamos `HiddenField(default=CurrentUserDefault())` aqui: esse field
    parece a solução óbvia, mas o DRF pula silenciosamente qualquer campo
    ausente do payload quando `partial=True` (é o que faz PATCH parcial
    funcionar) — inclusive campos com `default`. Ou seja, num PATCH,
    `updated_by` simplesmente não apareceria em `validated_data`, e o
    `update()` nunca o atualizaria. Por isso o preenchimento é feito
    explicitamente em `create()`/`update()`, não declarativamente.
    """

    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    updated_by = serializers.PrimaryKeyRelatedField(read_only=True)

    def create(self, validated_data):
        user = self.context["request"].user
        validated_data["created_by"] = user
        validated_data["updated_by"] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data["updated_by"] = self.context["request"].user
        return super().update(instance, validated_data)
