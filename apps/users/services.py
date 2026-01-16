import logging
import random

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils.timezone import now
from rest_framework_simplejwt.tokens import RefreshToken

from .tasks import send_otp_email, write_audit_log

User = get_user_model()
logger = logging.getLogger(__name__)


class OTPService:
    OTP_TTL = 300  
    EMAIL_RATE_LIMIT = 3
    EMAIL_RATE_WINDOW = 600  
    IP_RATE_LIMIT = 10
    IP_RATE_WINDOW = 3600  
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_DURATION = 900  

    @staticmethod
    def generate_otp():
        """Generate 6-digit OTP"""
        return str(random.randint(100000, 999999))

    @staticmethod
    def get_ttl(key):
        """Calculate TTL for a cache key."""
        timeout_at = cache.get(key + ':timeout')
        if timeout_at:  
            return max(0, timeout_at - int(now().timestamp()))
        return None

    @staticmethod
    def check_rate_limit(email, ip_address):
        """Check rate limits, return (is_limited, error_response_data)"""
        email_key = f"otp_request_email:{email}"
        ip_key = f"otp_request_ip:{ip_address}"
        
        email_count = cache.get(email_key, 0)
        if email_count >= OTPService.EMAIL_RATE_LIMIT:
            ttl = OTPService.get_ttl(email_key) or OTPService.EMAIL_RATE_WINDOW
            return True, {'error': 'Too many OTP requests. Please try again later.', 'retry_after': ttl}
        
        ip_count = cache.get(ip_key, 0)
        if ip_count >= OTPService.IP_RATE_LIMIT:
            ttl = OTPService.get_ttl(ip_key) or OTPService.IP_RATE_WINDOW
            return True, {'error': 'Too many OTP requests from this IP. Please try again later.', 'retry_after': ttl}
        
        return False, None

    @staticmethod
    def increment_rate_limit(email, ip_address):
        """Increment rate limit counters atomically"""
        email_key = f"otp_request_email:{email}"
        ip_key = f"otp_request_ip:{ip_address}"
        
        if cache.get(email_key) is None:
            cache.set(email_key, 1, timeout=OTPService.EMAIL_RATE_WINDOW)
            cache.set(email_key + ':timeout', int(now().timestamp()) + OTPService.EMAIL_RATE_WINDOW)
        else:
            cache.incr(email_key)
        
        if cache.get(ip_key) is None:
            cache.set(ip_key, 1, timeout=OTPService.IP_RATE_WINDOW)
            cache.set(ip_key + ':timeout', int(now().timestamp()) + OTPService.IP_RATE_WINDOW)
        else:
            cache.incr(ip_key)

    @staticmethod
    def store_otp(email, otp):
        """Store OTP in Redis"""
        cache.set(f"otp:{email}", otp, timeout=OTPService.OTP_TTL)

    @staticmethod
    def request_otp(email, ip_address, user_agent):
        """Request OTP - main business logic"""
        is_limited, error_data = OTPService.check_rate_limit(email, ip_address)
        if is_limited:
            logger.warning(f"⚠️ Rate limit exceeded for: {email}")
            write_audit_log.delay('OTP_REQUESTED', email, ip_address, {
                'user_agent': user_agent,
                'details': {'rate_limited': True}
            })
            return False, error_data
        
        otp = OTPService.generate_otp()
        OTPService.store_otp(email, otp)
        OTPService.increment_rate_limit(email, ip_address)
        
        send_otp_email.delay(email, otp)
        write_audit_log.delay('OTP_REQUESTED', email, ip_address, {
            'user_agent': user_agent,
            'details': {'otp_expiry_seconds': OTPService.OTP_TTL}
        })
        
        logger.info(f"✅ OTP requested for: {email}")
        return True, {'message': 'OTP sent successfully', 'expires_in': OTPService.OTP_TTL}

    @staticmethod
    def check_lockout(email):
        """Check if account is locked, return (is_locked, error_response_data)"""
        lockout_key = f"otp_lockout:{email}"
        if cache.get(lockout_key):
            ttl = OTPService.get_ttl(lockout_key) or OTPService.LOCKOUT_DURATION
            return True, {'error': 'Account temporarily locked due to too many failed attempts', 'unlock_eta': ttl}
        return False, None

    @staticmethod
    def verify_otp(email, otp, ip_address, user_agent):
        """Verify OTP - main business logic"""
        is_locked, error_data = OTPService.check_lockout(email)
        if is_locked:
            logger.warning(f"🔒 Account locked for: {email}")
            write_audit_log.delay('OTP_LOCKED', email, ip_address, {
                'user_agent': user_agent,
                'details': {'unlock_eta_seconds': error_data['unlock_eta']}
            })
            return False, error_data, 423
        
        stored_otp = cache.get(f"otp:{email}")
        if not stored_otp:
            logger.warning(f"⚠️ No OTP found for: {email}")
            return False, {'error': 'OTP not found or expired. Please request a new one.'}, 400
        
        if stored_otp != otp:
            return OTPService._handle_failed_attempt(email, ip_address, user_agent)
        
        return OTPService._handle_successful_verification(email, ip_address, user_agent)

    @staticmethod
    def _handle_failed_attempt(email, ip_address, user_agent):
        
        failed_key = f"otp_failed:{email}"
        failed_count = cache.get(failed_key, 0) + 1
        
        if failed_count >= OTPService.MAX_FAILED_ATTEMPTS:
            cache.set(f"otp_lockout:{email}", True, timeout=OTPService.LOCKOUT_DURATION)
            cache.delete(failed_key)
            cache.delete(f"otp:{email}")
            
            logger.error(f"🔒 Account locked after {OTPService.MAX_FAILED_ATTEMPTS} failed attempts: {email}")
            write_audit_log.delay('OTP_LOCKED', email, ip_address, {
                'user_agent': user_agent,
                'details': {'reason': 'max_attempts_exceeded', 'unlock_eta_seconds': OTPService.LOCKOUT_DURATION}
            })
            return False, {
                'error': f'Too many failed attempts. Account locked for {OTPService.LOCKOUT_DURATION // 60} minutes.',
                'unlock_eta': OTPService.LOCKOUT_DURATION
            }, 423
        
        if cache.get(failed_key) is None:
            cache.set(failed_key, failed_count, timeout=OTPService.LOCKOUT_DURATION)
        else:
            cache.set(failed_key, failed_count, timeout=cache.ttl(failed_key))
        
        logger.warning(f"❌ Invalid OTP attempt {failed_count}/{OTPService.MAX_FAILED_ATTEMPTS} for: {email}")
        write_audit_log.delay('OTP_FAILED', email, ip_address, {
            'user_agent': user_agent,
            'details': {'attempt': failed_count, 'remaining': OTPService.MAX_FAILED_ATTEMPTS - failed_count}
        })
        return False, {
            'error': 'Invalid OTP',
            'attempts_remaining': OTPService.MAX_FAILED_ATTEMPTS - failed_count
        }, 400

    @staticmethod
    def _handle_successful_verification(email, ip_address, user_agent):
       
        cache.delete(f"otp:{email}")
        cache.delete(f"otp_failed:{email}")
        
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email.split('@')[0],
                'first_name': email.split('@')[0],
                'last_name': 'User',
                'is_verified': True
            }
        )
        
        if not created:
            user.is_verified = True
            user.save(update_fields=['is_verified'])
        
        refresh = RefreshToken.for_user(user)
        
        logger.info(f"✅ OTP verified successfully for: {email}")
        write_audit_log.delay('OTP_VERIFIED', email, ip_address, {
            'user_agent': user_agent,
            'details': {'user_created': created}
        })
        
        return True, {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': str(user.id),
                'email': user.email,
                'username': user.username,
                'is_verified': user.is_verified
            }
        }, 200
