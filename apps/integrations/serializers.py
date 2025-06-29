from rest_framework import serializers
from .models import IntegrationProvider, WebhookEvent, ExternalAPICall, IntegrationHealth


class IntegrationProviderSerializer(serializers.ModelSerializer):
    """Serializer for IntegrationProvider model."""
    
    class Meta:
        model = IntegrationProvider
        fields = [
            'id', 'name', 'webhook_url', 'api_base_url', 'auth_type',
            'config', 'is_active', 'rate_limit_per_minute', 'burst_limit',
            'max_retries', 'backoff_multiplier', 'max_backoff_seconds',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'secret_key': {'write_only': True}
        }


class WebhookEventSerializer(serializers.ModelSerializer):
    """Serializer for WebhookEvent model."""
    
    provider_name = serializers.ReadOnlyField(source='provider.name')
    
    class Meta:
        model = WebhookEvent
        fields = [
            'id', 'provider', 'provider_name', 'event_type', 'event_id',
            'organization_id', 'data', 'metadata', 'status', 'retry_count',
            'error_message', 'received_at', 'processed_at', 'next_retry_at',
            'source_ip', 'headers'
        ]
        read_only_fields = [
            'id', 'provider_name', 'received_at', 'processed_at', 
            'next_retry_at', 'source_ip', 'headers'
        ]


class ExternalAPICallSerializer(serializers.ModelSerializer):
    """Serializer for ExternalAPICall model."""
    
    provider_name = serializers.ReadOnlyField(source='provider.name')
    user_email = serializers.ReadOnlyField(source='user.email')
    
    class Meta:
        model = ExternalAPICall
        fields = [
            'id', 'provider', 'provider_name', 'endpoint', 'method',
            'request_data', 'response_data', 'response_status', 'status',
            'started_at', 'completed_at', 'duration_ms', 'error_message',
            'retry_count', 'correlation_id', 'user', 'user_email'
        ]
        read_only_fields = [
            'id', 'provider_name', 'user_email', 'started_at', 'completed_at',
            'duration_ms', 'duration_ms'
        ]


class IntegrationHealthSerializer(serializers.ModelSerializer):
    """Serializer for IntegrationHealth model."""
    
    provider_name = serializers.ReadOnlyField(source='provider.name')
    
    class Meta:
        model = IntegrationHealth
        fields = [
            'id', 'provider', 'provider_name', 'is_healthy', 'last_check_at',
            'response_time_ms', 'consecutive_failures', 'last_error_message',
            'circuit_breaker_state'
        ]
        read_only_fields = [
            'id', 'provider_name', 'last_check_at', 'response_time_ms',
            'consecutive_failures', 'last_error_message'
        ]


class WebhookEventCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating webhook events."""
    
    class Meta:
        model = WebhookEvent
        fields = [
            'provider', 'event_type', 'event_id', 'organization_id',
            'data', 'metadata', 'source_ip', 'headers'
        ]


class ExternalAPICallCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating external API calls."""
    
    class Meta:
        model = ExternalAPICall
        fields = [
            'provider', 'endpoint', 'method', 'request_data',
            'correlation_id', 'user'
        ]
        read_only_fields = ['user']


class IntegrationProviderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating integration providers."""
    
    class Meta:
        model = IntegrationProvider
        fields = [
            'name', 'webhook_url', 'api_base_url', 'auth_type', 'secret_key',
            'config', 'rate_limit_per_minute', 'burst_limit', 'max_retries',
            'backoff_multiplier', 'max_backoff_seconds'
        ]
        extra_kwargs = {
            'secret_key': {'write_only': True}
        }


class WebhookEventRetrySerializer(serializers.Serializer):
    """Serializer for retrying webhook events."""
    
    force = serializers.BooleanField(default=False, help_text="Force retry even if max retries exceeded")


class CircuitBreakerStatusSerializer(serializers.Serializer):
    """Serializer for circuit breaker status."""
    
    provider_name = serializers.CharField()
    state = serializers.CharField()
    failure_count = serializers.IntegerField()
    last_failure_time = serializers.DateTimeField(allow_null=True)
    threshold = serializers.IntegerField()
    timeout = serializers.IntegerField()
