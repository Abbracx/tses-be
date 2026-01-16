from django.contrib.auth import get_user_model
from django.db import models

from apps.common.models import TimeStampedModel

User = get_user_model()


class AuditLog(TimeStampedModel):
    ACTION_CHOICES = [
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('OTP_REQUESTED', 'OTP Requested'),
        ('OTP_VERIFIED', 'OTP Verified'),
        ('OTP_FAILED', 'OTP Failed'),
        ('OTP_LOCKED', 'OTP Locked'),
        ('USER_CREATE', 'User Create'),
        ('USER_UPDATE', 'User Update'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='audit_logs', db_index=True, null=True, blank=True)
    email = models.EmailField(db_index=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, db_index=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    details = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email', 'action']),
            models.Index(fields=['action', 'created_at']),
            models.Index(fields=['email', 'created_at']),
        ]

    def __str__(self):
        return f"{self.email} - {self.action} - {self.created_at}"
