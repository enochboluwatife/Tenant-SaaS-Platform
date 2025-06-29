from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import IntegrationProvider, WebhookEvent, ExternalAPICall, IntegrationHealth
from .serializers import (
    IntegrationProviderSerializer, WebhookEventSerializer, 
    ExternalAPICallSerializer, IntegrationHealthSerializer
)
from .webhook_handlers import (
    handle_user_service_webhook, handle_payment_service_webhook, 
    handle_communication_service_webhook
)
from .circuit_breaker import CircuitBreaker
from apps.audit.models import AuditLog
import json


class IntegrationProviderViewSet(viewsets.ModelViewSet):
    """ViewSet for integration provider management."""
    
    queryset = IntegrationProvider.objects.all()
    serializer_class = IntegrationProviderSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['name', 'is_active']
    search_fields = ['name', 'api_base_url']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class WebhookEventViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for webhook event management."""
    
    queryset = WebhookEvent.objects.all()
    serializer_class = WebhookEventSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['provider', 'status', 'event_type']
    search_fields = ['event_id', 'organization_id']
    ordering_fields = ['received_at', 'processed_at']
    ordering = ['-received_at']
    
    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """Retry processing a failed webhook event."""
        event = self.get_object()
        
        if event.status == 'failed':
            # Reset event for retry
            event.status = 'pending'
            event.retry_count = 0
            event.error_message = ''
            event.save()
            
            # Log the retry action
            AuditLog.log_action(
                user=request.user,
                tenant=None,
                action='API_CALL',
                resource_type='WebhookEvent',
                resource_id=str(event.id),
                new_values={'retry_requested': True},
                request=request
            )
            
            return Response({'status': 'Event queued for retry'})
        else:
            return Response(
                {'error': 'Only failed events can be retried'}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class ExternalAPICallViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for external API call monitoring."""
    
    queryset = ExternalAPICall.objects.all()
    serializer_class = ExternalAPICallSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['provider', 'status', 'method']
    search_fields = ['endpoint', 'correlation_id']
    ordering_fields = ['started_at', 'completed_at', 'duration_ms']
    ordering = ['-started_at']


class IntegrationHealthViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for integration health monitoring."""
    
    queryset = IntegrationHealth.objects.all()
    serializer_class = IntegrationHealthSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['is_healthy', 'circuit_breaker_state']
    ordering_fields = ['last_check_at']
    ordering = ['-last_check_at']


class CircuitBreakerStatusView(APIView):
    """View for circuit breaker status."""
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """Get circuit breaker status for all providers."""
        providers = IntegrationProvider.objects.filter(is_active=True)
        status_data = {}
        
        for provider in providers:
            circuit_breaker = CircuitBreaker(provider.name)
            status_data[provider.name] = {
                'state': circuit_breaker.state,
                'failure_count': circuit_breaker.failure_count,
                'last_failure_time': circuit_breaker.last_failure_time,
                'threshold': circuit_breaker.threshold,
                'timeout': circuit_breaker.timeout,
            }
        
        return Response(status_data)


class UserServiceWebhookView(APIView):
    """Webhook endpoint for user service events."""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Handle user service webhook events."""
        try:
            # Validate webhook signature (simplified)
            if not self._validate_signature(request):
                return Response({'error': 'Invalid signature'}, status=status.HTTP_401_UNAUTHORIZED)
            
            # Process the webhook
            event_data = request.data
            result = handle_user_service_webhook(event_data, request)
            
            # Log the webhook
            AuditLog.log_action(
                user=None,
                tenant=None,
                action='WEBHOOK',
                resource_type='UserService',
                resource_id=event_data.get('event_id', ''),
                new_values=event_data,
                request=request
            )
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _validate_signature(self, request):
        """Validate webhook signature (simplified implementation)."""
        # In production, implement proper signature validation
        return True


class PaymentServiceWebhookView(APIView):
    """Webhook endpoint for payment service events."""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Handle payment service webhook events."""
        try:
            # Validate webhook signature
            if not self._validate_signature(request):
                return Response({'error': 'Invalid signature'}, status=status.HTTP_401_UNAUTHORIZED)
            
            # Process the webhook
            event_data = request.data
            result = handle_payment_service_webhook(event_data, request)
            
            # Log the webhook
            AuditLog.log_action(
                user=None,
                tenant=None,
                action='WEBHOOK',
                resource_type='PaymentService',
                resource_id=event_data.get('event_id', ''),
                new_values=event_data,
                request=request
            )
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _validate_signature(self, request):
        """Validate webhook signature (simplified implementation)."""
        # In production, implement proper signature validation
        return True


class CommunicationServiceWebhookView(APIView):
    """Webhook endpoint for communication service events."""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Handle communication service webhook events."""
        try:
            # Validate webhook signature
            if not self._validate_signature(request):
                return Response({'error': 'Invalid signature'}, status=status.HTTP_401_UNAUTHORIZED)
            
            # Process the webhook
            event_data = request.data
            result = handle_communication_service_webhook(event_data, request)
            
            # Log the webhook
            AuditLog.log_action(
                user=None,
                tenant=None,
                action='WEBHOOK',
                resource_type='CommunicationService',
                resource_id=event_data.get('event_id', ''),
                new_values=event_data,
                request=request
            )
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _validate_signature(self, request):
        """Validate webhook signature (simplified implementation)."""
        # In production, implement proper signature validation
        return True
