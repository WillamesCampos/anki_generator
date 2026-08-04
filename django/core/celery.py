"""
Fundação Celery + RabbitMQ (broker) + Redis (result backend).

Sprint 0 entrega só a infraestrutura (app Celery configurado, sem tasks reais
ainda) — ver tasks.md da change `migrate-to-django-microservices-architecture`,
tarefa 5.4. A publicação de eventos assíncrona de verdade (IA, WhatsApp,
relatórios) é adicionada nas sprints correspondentes do PRD.
"""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.local")

app = Celery("anki_generator")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
