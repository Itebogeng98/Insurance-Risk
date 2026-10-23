from django.contrib import admin

from .models import AuditLog, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user', 'action', 'object_type', 'object_id', 'ip_address')
    list_filter = ('action', 'object_type')
    search_fields = ('user__username', 'object_type', 'object_id', 'detail')
    readonly_fields = ('created_at',)

# Register your models here.
