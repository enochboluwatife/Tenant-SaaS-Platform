from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid


class Tenant(models.Model):
    """Multi-tenant organization model with data isolation."""
    
    PLAN_CHOICES = [
        ('basic', 'Basic'),
        ('premium', 'Premium'),
        ('enterprise', 'Enterprise'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    domain = models.CharField(max_length=255, unique=True)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='basic')
    employee_count = models.PositiveIntegerField(default=0)
    
    # SSO Configuration (JSON field for flexibility)
    sso_config = models.JSONField(default=dict, blank=True)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'tenants'
        verbose_name = 'Tenant'
        verbose_name_plural = 'Tenants'
    
    def __str__(self):
        return f"{self.name} ({self.domain})"
    
    @property
    def subscription_status(self):
        """Get subscription status based on plan and payment info."""
        # This would integrate with payment service
        return 'active' if self.is_active else 'inactive'


class TenantUser(AbstractUser):
    """Extended user model with tenant association."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='users', null=True, blank=True)
    department = models.CharField(max_length=100, blank=True)
    title = models.CharField(max_length=100, blank=True)
    
    # SSO attributes for external identity providers
    sso_attributes = models.JSONField(default=dict, blank=True)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'tenant_users'
        verbose_name = 'Tenant User'
        verbose_name_plural = 'Tenant Users'
        unique_together = [['tenant', 'email']]
    
    def __str__(self):
        return f"{self.email} ({self.tenant.name if self.tenant else 'System'})"
    
    def save(self, *args, **kwargs):
        # Ensure username is set to email if not provided
        if not self.username:
            self.username = self.email
        super().save(*args, **kwargs)
