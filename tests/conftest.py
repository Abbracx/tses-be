import os

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

# Set test settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tses_be.settings.test')

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_factory():
    def create_user(**kwargs):
        defaults = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'testpass123'
        }
        defaults.update(kwargs)
        return User.objects.create_user(**defaults)
    return create_user


@pytest.fixture
def admin_user():
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        first_name='Admin',
        last_name='User',
        password='adminpass123'
    )


@pytest.fixture
def regular_user():
    return User.objects.create_user(
        username='regular',
        email='regular@example.com',
        first_name='Regular',
        last_name='User',
        password='regularpass123'
    )
