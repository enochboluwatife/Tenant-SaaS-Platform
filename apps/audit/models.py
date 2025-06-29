from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone
import uuid
import json
import logging

User = get_user_model()


class AuditLog(models.Model):
    """Comprehensive audit logging for all data modifications."""
    
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('API_CALL', 'API Call'),
        ('WEBHOOK', 'Webhook'),
        ('EXPORT', 'Export'),
        ('IMPORT', 'Import'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # User and tenant context
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, null=True, blank=True, related_name='audit_logs')
    
    # Action details
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    resource_type = models.CharField(max_length=100, blank=True)  # Model name
    resource_id = models.CharField(max_length=100, blank=True)    # Object ID
    
    # Content type for generic relations
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.CharField(max_length=100, null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Data changes
    old_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    
    # Request context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    request_path = models.CharField(max_length=500, blank=True)
    request_method = models.CharField(max_length=10, blank=True)
    
    # Metadata
    timestamp = models.DateTimeField(auto_now_add=True)
    session_id = models.CharField(max_length=100, null=True, blank=True)
    correlation_id = models.CharField(max_length=100, blank=True)  # For tracking related actions
    
    class Meta:
        db_table = 'audit_logs'
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        indexes = [
            models.Index(fields=['tenant', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['correlation_id']),
        ]
    
    def __str__(self):
        return f"{self.action} by {self.user.email if self.user else 'System'} at {self.timestamp}"
    
    @classmethod
    def log_action(cls, user=None, tenant=None, action='', resource_type='', resource_id='', 
                   old_values=None, new_values=None, request=None, **kwargs):
        """Convenience method to create audit log entries."""
        
        # Handle anonymous users
        if user and user.is_anonymous:
            user = None
        
        audit_log = cls(
            user=user,
            tenant=tenant,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values or {},
            new_values=new_values or {},
            **kwargs
        )
        
        # Extract request information if provided
        if request:
            audit_log.ip_address = cls.get_client_ip(request)
            audit_log.user_agent = request.META.get('HTTP_USER_AGENT', '')
            audit_log.request_path = request.path
            audit_log.request_method = request.method
            # Only set session_id if session exists and has a key
            if hasattr(request, 'session') and request.session and request.session.session_key:
                audit_log.session_id = request.session.session_key
        
        try:
            audit_log.save()
            return audit_log
        except Exception as e:
            # Log the error but don't break the main functionality
            logger = logging.getLogger(__name__)
            logger.error(f"Audit logging error: {e}")
            return None
    
    @staticmethod
    def get_client_ip(request):
        """Extract client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class AuditLogEntry(models.Model):
    """Detailed audit log entries for complex operations."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    audit_log = models.ForeignKey(AuditLog, on_delete=models.CASCADE, related_name='entries')
    
    # Entry details
    field_name = models.CharField(max_length=100, blank=True)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    
    # Metadata
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'audit_log_entries'
        verbose_name = 'Audit Log Entry'
        verbose_name_plural = 'Audit Log Entries'
    
    def __str__(self):
        return f"Field change: {self.field_name} in {self.audit_log}"
