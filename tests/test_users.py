import pytest
from django.urls import reverse
from rest_framework import status
from unittest.mock import patch
from tests.factories import UserFactory

@pytest.mark.django_db
class TestUserManagement:
    def test_create_user(self, user_factory):
        user = user_factory(username='newuser', email='new@example.com')
        assert user.username == 'newuser'
        assert user.email == 'new@example.com'
        assert user.check_password('testpass123')

    def test_user_profile_access(self, api_client, regular_user):
        api_client.force_authenticate(user=regular_user)
        url = reverse('usersapi:users-me')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == regular_user.email

    def test_admin_user_access(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        url = reverse('usersapi:users-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data.get("results", None), list)
        assert len(response.data) > 0

    def test_request_otp(self, api_client):
        user = UserFactory(email='testuser@example.com')
        url = reverse('usersotp:otp-request')
        data = {'email': user.email}
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert 'message' in response.data
        assert response.data['message'] == 'OTP sent successfully'

    def test_verify_otp(self, api_client):
        with patch('apps.users.services.OTPService.request_otp') as mock_request_otp, \
             patch('apps.users.services.OTPService.verify_otp') as mock_verify_otp:
            
            mock_request_otp.return_value = (True, {'message': 'OTP sent successfully', 'expires_in': 300})
            mock_verify_otp.return_value = (
                True,
                {
                    'access': 'mock_access_token',
                    'refresh': 'mock_refresh_token'
                },
                200
            )
            
            user = UserFactory(email='testuser@example.com')
            request_url = reverse('usersotp:otp-request')
            request_data = {'email': user.email}
            response = api_client.post(request_url, request_data)
            assert response.status_code == status.HTTP_202_ACCEPTED
            assert response.data['message'] == 'OTP sent successfully'

            verify_url = reverse('usersotp:otp-verify')
            verify_data = {'email': user.email, 'otp': '123456'}
            response = api_client.post(verify_url, verify_data)
            assert response.status_code == status.HTTP_200_OK
            assert 'access' in response.data
            assert 'refresh' in response.data

    def test_user_list_cache(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        url = reverse('usersapi:users-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data.get("results", None), list)

        # Simulate cache hit
        cached_response = api_client.get(url)
        assert cached_response.status_code == status.HTTP_200_OK
        assert cached_response.data == response.data