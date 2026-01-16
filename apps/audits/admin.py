from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['email', 'action', 'ip_address', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['email', 'ip_address']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
