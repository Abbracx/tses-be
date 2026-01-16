import pytest
from datetime import datetime, timedelta
from apps.audits.models import AuditLog
from apps.audits.services import AuditService
from tests.factories import UserFactory

@pytest.mark.django_db
class TestAuditService:
    def test_filter_audit_logs(self, user_factory):
        # Create a user and audit logs
        user = user_factory(username="testuser")
        AuditLog.objects.create(user=user, action="LOGIN", created_at=datetime.now() - timedelta(days=1))
        AuditLog.objects.create(user=user, action="LOGOUT", created_at=datetime.now())
        
        queryset = AuditLog.objects.all()
        query_params = {
            'from': (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d'),
            'to': datetime.now().strftime('%Y-%m-%d'),
            'event': 'LOGIN'
        }
        
        filtered_logs = AuditService.filter_audit_logs(queryset, query_params)
        assert filtered_logs.count() == 0
        assert filtered_logs.first().action == "LOGIN"