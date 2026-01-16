import pytest
from unittest.mock import patch
from django.core.cache import cache
from apps.users.services import OTPService
from tests.factories import UserFactory

@pytest.mark.django_db
class TestOTPService:
    def test_generate_otp(self):
        otp = OTPService.generate_otp()
        assert len(otp) == 6
        assert otp.isdigit()

    def test_store_otp(self):
        email = "testuser@example.com"
        otp = "123456"
        OTPService.store_otp(email, otp)
        cached_otp = cache.get(f"otp:{email}")
        assert cached_otp == otp

    def test_check_rate_limit(self):
        email = "testuser@example.com"
        ip_address = "127.0.0.1"
        cache.clear()  
        OTPService.increment_rate_limit(email, ip_address)
        is_limited, _ = OTPService.check_rate_limit(email, ip_address)
        assert not is_limited

    def test_request_otp(self, api_client):
        user = UserFactory(email="testuser@example.com")
        ip_address = "127.0.0.1"
        user_agent = "TestAgent"
        
        cache.clear() 
        
        with patch('apps.users.services.send_otp_email.delay') as mock_send_email, \
            patch('apps.users.services.write_audit_log.delay') as mock_write_log:
            
            success, response_data = OTPService.request_otp(user.email, ip_address, user_agent)
            assert success
            assert response_data['message'] == "OTP sent successfully"

            mock_send_email.assert_called_once_with(user.email, mock_send_email.call_args[0][1])
            mock_write_log.assert_called_once()

    def test_verify_otp(self, api_client):
        user = UserFactory(email="testuser@example.com")
        otp = "123456"
        ip_address = "127.0.0.1"
        user_agent = "TestAgent"
        
        OTPService.store_otp(user.email, otp)
        
        with patch('apps.users.services.write_audit_log.delay') as mock_write_log:
            success, response_data, status_code = OTPService.verify_otp(user.email, otp, ip_address, user_agent)
            assert success
            assert 'access' in response_data
            assert 'refresh' in response_data
            assert status_code == 200
            mock_write_log.assert_called_once()