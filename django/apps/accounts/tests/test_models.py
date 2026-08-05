import pytest
from django.db import IntegrityError, transaction

from apps.accounts.models import User


@pytest.mark.django_db
def test_email_is_required_and_unique():
    User.objects.create_user(username="first", email="dup@example.com", password="x")

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            User.objects.create_user(username="second", email="dup@example.com", password="x")


@pytest.mark.django_db
def test_user_authenticates_via_email():
    user = User.objects.create_user(username="someone", email="someone@example.com", password="x")

    assert User.USERNAME_FIELD == "email"
    assert User.objects.get(email="someone@example.com") == user
