import logging

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions
from rest_framework.filters import OrderingFilter
from rest_framework.pagination import PageNumberPagination

from apps.audits.models import AuditLog
from apps.audits.paginations import AuditLogPagination
from apps.audits.serializers import AuditLogSerializer
from apps.audits.services import AuditService

logger = logging.getLogger(__name__)



class AuditLogListView(generics.ListAPIView):
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = AuditLogPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['email', 'action']
    ordering = ['-created_at']
    ordering_fields = ['created_at', 'action']
    
    def get_queryset(self):
        queryset = AuditLog.objects.all()
        queryset = AuditService.filter_audit_logs(queryset, self.request.query_params)
        logger.info(f"Audit logs accessed by user: {self.request.user.email}")
        return queryset
