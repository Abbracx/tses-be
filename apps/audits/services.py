from django.db.models import Q

# from .models import AuditLog


class AuditService:
    @staticmethod
    def filter_audit_logs(queryset, query_params):
        """Apply filters to audit log queryset"""
        from_date = query_params.get('from')
        to_date = query_params.get('to')
        event = query_params.get('event')
        
        if from_date:
            queryset = queryset.filter(created_at__gte=from_date)
        if to_date:
            queryset = queryset.filter(created_at__lte=to_date)
        if event:
            queryset = queryset.filter(action=event)
            
        return queryset
