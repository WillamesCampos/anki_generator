"""
Signal de atribuição automática ao grupo `standard_user` (Sprint 5).

Um único `post_save` no `User`, em vez de um hook por fluxo de criação
(Google, e-mail/senha, seed) — qualquer caminho que crie um `User` (incluindo
`User.objects.get_or_create`, usado pelo seed) dispara `save()` e, com isso,
este signal, sem precisar duplicar a atribuição em cada view/comando.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver

from .groups import STANDARD_USER_GROUP

User = get_user_model()


@receiver(post_save, sender=User)
def assign_standard_user_group(sender, instance, created, **kwargs):
    if not created:
        return

    group, _ = Group.objects.get_or_create(name=STANDARD_USER_GROUP)
    instance.groups.add(group)
