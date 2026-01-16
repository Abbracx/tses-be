import pytest
from datetime import timedelta
from django.utils.timezone import now
from apps.audits.models import AuditLog
from apps.audits.services import AuditService


@pytest.mark.django_db
class TestAuditService:
    def test_filter_audit_logs(self, user_factory):
        user = user_factory(username="testuser")
        AuditLog.objects.create(user=user, action="LOGIN", created_at=now() - timedelta(days=1))
        AuditLog.objects.create(user=user, action="LOGOUT", created_at=now())
        
        queryset = AuditLog.objects.all()
        query_params = {
            'from': (now() - timedelta(days=2)),
            'to': now(),
            'event': 'LOGIN'
        }
        
        filtered_logs = AuditService.filter_audit_logs(queryset, query_params)
        assert filtered_logs.count() == 1
        assert filtered_logs.first().action == "LOGIN"