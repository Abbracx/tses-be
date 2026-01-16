from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    event = serializers.CharField(source='action', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = ['id', 'email', 'event', 'action', 'ip_address', 'user_agent', 'details', 'created_at']
        read_only_fields = fields
