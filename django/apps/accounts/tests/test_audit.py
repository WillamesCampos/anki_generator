import pytest
from rest_framework import serializers

from apps.accounts.audit import AuditSerializerMixin
from apps.accounts.models import User
from apps.accounts.tests.conftest import Widget


class WidgetSerializer(AuditSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Widget
        fields = ["id", "name", "owner", "created_by", "updated_by"]


@pytest.mark.django_db(transaction=True)
def test_created_by_is_set_from_request_user_not_client_input(widget_table, rf):
    owner = User.objects.create_user(username="w_owner", email="w_owner@example.com")
    attacker = User.objects.create_user(username="w_attacker", email="w_attacker@example.com")

    request = rf.post("/")
    request.user = owner

    serializer = WidgetSerializer(
        data={"name": "x", "owner": owner.id, "created_by": attacker.id},
        context={"request": request},
    )
    serializer.is_valid(raise_exception=True)
    instance = serializer.save()

    assert instance.created_by_id == owner.id
    assert instance.created_by_id != attacker.id


@pytest.mark.django_db(transaction=True)
def test_updated_by_is_refreshed_on_update(widget_table, rf):
    owner = User.objects.create_user(username="w_owner2", email="w_owner2@example.com")
    other = User.objects.create_user(username="w_other2", email="w_other2@example.com")

    widget = Widget.objects.create(owner=owner, name="original", created_by=owner, updated_by=owner)

    request = rf.patch("/")
    request.user = other

    serializer = WidgetSerializer(
        instance=widget,
        data={"name": "changed"},
        partial=True,
        context={"request": request},
    )
    serializer.is_valid(raise_exception=True)
    updated = serializer.save()

    assert updated.updated_by_id == other.id
