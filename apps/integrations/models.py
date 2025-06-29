from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid
import json

User = get_user_model()


class IntegrationProvider(models.Model):
    """External service integration providers."""
    
    PROVIDER_CHOICES = [
        ('user_service', 'User Management Service'),
        ('payment_service', 'Payment Service'),
        ('communication_service', 'Communication Service'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, choices=PROVIDER_CHOICES)
    webhook_url = models.CharField(max_length=500)
    api_base_url = models.URLField()
    auth_type = models.CharField(max_length=20, choices=[
        ('api_key', 'API Key'),
        ('oauth2', 'OAuth2'),
        ('bearer_token', 'Bearer Token'),
    ])
    secret_key = models.CharField(max_length=255)
    
    # Configuration
    config = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    
    # Rate limiting
    rate_limit_per_minute = models.PositiveIntegerField(default=100)
    burst_limit = models.PositiveIntegerField(default=20)
    
    # Retry policy
    max_retries = models.PositiveIntegerField(default=3)
    backoff_multiplier = models.FloatField(default=2.0)
    max_backoff_seconds = models.PositiveIntegerField(default=300)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'integration_providers'
        verbose_name = 'Integration Provider'
        verbose_name_plural = 'Integration Providers'
    
    def __str__(self):
        return f"{self.get_name_display()} ({self.api_base_url})"


class WebhookEvent(models.Model):
    """Incoming webhook events from external services."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('retry', 'Retry'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey(IntegrationProvider, on_delete=models.CASCADE, related_name='webhook_events')
    
    # Event details
    event_type = models.CharField(max_length=100)
    event_id = models.CharField(max_length=100, unique=True)
    organization_id = models.CharField(max_length=100, blank=True)  # External org ID
    
    # Event data
    data = models.JSONField(default=dict)
    metadata = models.JSONField(default=dict)
    
    # Processing status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    retry_count = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    
    # Timing
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    next_retry_at = models.DateTimeField(null=True, blank=True)
    
    # Request context
    source_ip = models.GenericIPAddressField(null=True, blank=True)
    headers = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'webhook_events'
        verbose_name = 'Webhook Event'
        verbose_name_plural = 'Webhook Events'
        indexes = [
            models.Index(fields=['provider', 'status']),
            models.Index(fields=['event_type', 'received_at']),
            models.Index(fields=['next_retry_at']),
        ]
    
    def __str__(self):
        return f"{self.event_type} from {self.provider.name} ({self.status})"
    
    def mark_processing(self):
        """Mark event as being processed."""
        self.status = 'processing'
        self.save(update_fields=['status'])
    
    def mark_completed(self):
        """Mark event as successfully completed."""
        self.status = 'completed'
        self.processed_at = timezone.now()
        self.save(update_fields=['status', 'processed_at'])
    
    def mark_failed(self, error_message=''):
        """Mark event as failed."""
        self.status = 'failed'
        self.error_message = error_message
        self.processed_at = timezone.now()
        self.save(update_fields=['status', 'error_message', 'processed_at'])
    
    def schedule_retry(self):
        """Schedule event for retry."""
        if self.retry_count < self.provider.max_retries:
            self.retry_count += 1
            self.status = 'retry'
            
            # Calculate next retry time with exponential backoff
            backoff_seconds = min(
                self.provider.backoff_multiplier ** self.retry_count,
                self.provider.max_backoff_seconds
            )
            self.next_retry_at = timezone.now() + timezone.timedelta(seconds=backoff_seconds)
            
            self.save(update_fields=['retry_count', 'status', 'next_retry_at'])
            return True
        else:
            self.mark_failed('Max retries exceeded')
            return False


class ExternalAPICall(models.Model):
    """Track external API calls for monitoring and debugging."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey(IntegrationProvider, on_delete=models.CASCADE, related_name='api_calls')
    
    # API call details
    endpoint = models.CharField(max_length=500)
    method = models.CharField(max_length=10, choices=[
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('PATCH', 'PATCH'),
        ('DELETE', 'DELETE'),
    ])
    
    # Request/Response data
    request_data = models.JSONField(default=dict, blank=True)
    response_data = models.JSONField(default=dict, blank=True)
    response_status = models.PositiveIntegerField(null=True, blank=True)
    
    # Status and timing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_ms = models.PositiveIntegerField(null=True, blank=True)
    
    # Error handling
    error_message = models.TextField(blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    
    # Context
    correlation_id = models.CharField(max_length=100, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='api_calls')
    
    class Meta:
        db_table = 'external_api_calls'
        verbose_name = 'External API Call'
        verbose_name_plural = 'External API Calls'
        indexes = [
            models.Index(fields=['provider', 'status']),
            models.Index(fields=['started_at']),
            models.Index(fields=['correlation_id']),
        ]
    
    def __str__(self):
        return f"{self.method} {self.endpoint} ({self.status})"
    
    def mark_in_progress(self):
        """Mark API call as in progress."""
        self.status = 'in_progress'
        self.save(update_fields=['status'])
    
    def mark_completed(self, response_data=None, response_status=None):
        """Mark API call as completed."""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.duration_ms = int((self.completed_at - self.started_at).total_seconds() * 1000)
        
        if response_data is not None:
            self.response_data = response_data
        if response_status is not None:
            self.response_status = response_status
            
        self.save(update_fields=['status', 'completed_at', 'duration_ms', 'response_data', 'response_status'])
    
    def mark_failed(self, error_message=''):
        """Mark API call as failed."""
        self.status = 'failed'
        self.completed_at = timezone.now()
        self.duration_ms = int((self.completed_at - self.started_at).total_seconds() * 1000)
        self.error_message = error_message
        self.save(update_fields=['status', 'completed_at', 'duration_ms', 'error_message'])


class IntegrationHealth(models.Model):
    """Monitor integration health and status."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey(IntegrationProvider, on_delete=models.CASCADE, related_name='health_checks')
    
    # Health status
    is_healthy = models.BooleanField(default=True)
    last_check_at = models.DateTimeField(auto_now_add=True)
    response_time_ms = models.PositiveIntegerField(null=True, blank=True)
    
    # Error tracking
    consecutive_failures = models.PositiveIntegerField(default=0)
    last_error_message = models.TextField(blank=True)
    
    # Circuit breaker state
    circuit_breaker_state = models.CharField(max_length=20, choices=[
        ('closed', 'Closed'),
        ('open', 'Open'),
        ('half_open', 'Half Open'),
    ], default='closed')
    
    class Meta:
        db_table = 'integration_health'
        verbose_name = 'Integration Health'
        verbose_name_plural = 'Integration Health'
    
    def __str__(self):
        return f"Health check for {self.provider.name} ({'Healthy' if self.is_healthy else 'Unhealthy'})"
