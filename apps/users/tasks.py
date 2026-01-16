import logging

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(bind=True, max_retries=3)
def send_otp_email(self, email, otp):

    subject = "Your OTP Code"
    message = f"""
        Your OTP code is: {otp}

        This code will expire in 5 minutes.

        If you didn't request this code, please ignore this email.
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        logger.info(f"✅ [CELERY TASK] OTP email sent to: {email}")
        return f"OTP email sent to {email}"
    except Exception as e:
        logger.error(f"❌ [CELERY TASK] Failed to send OTP email to {email}: {str(e)}")
        raise self.retry(exc=e, countdown=60)


@shared_task
def write_audit_log(event, email, ip, meta):
    """
    Asynchronously write audit log entry
    
    Args:
        event: Action type (OTP_REQUESTED, OTP_VERIFIED, OTP_FAILED, OTP_LOCKED)
        email: User email
        ip: IP address
        meta: Additional metadata dict
    """
    from apps.audits.models import AuditLog
    
    try:
        user = None
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            pass
        
        AuditLog.objects.create(
            user=user,
            email=email,
            action=event,
            ip_address=ip,
            user_agent=meta.get('user_agent', ''),
            details=meta.get('details', {})
        )
        logger.info(f"✅ [CELERY TASK] Audit log created: {event} for {email}")
        return f"Audit log created for {email}"
    except Exception as e:
        logger.error(f"❌ [CELERY TASK] Failed to create audit log for {email}: {str(e)}")
        raise
