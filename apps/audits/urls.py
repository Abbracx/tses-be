from django.urls import path

from .views import AuditLogListView

app_name = 'audits'

urlpatterns = [
    path('logs/', AuditLogListView.as_view(), name='audit-logs'),
]
