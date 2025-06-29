from django.urls import path
from . import views

urlpatterns = [
    # Webhook endpoints
    path('webhooks/user-service/', views.UserServiceWebhookView.as_view(), name='user_service_webhook'),
    path('webhooks/payment-service/', views.PaymentServiceWebhookView.as_view(), name='payment_service_webhook'),
    path('webhooks/communication-service/', views.CommunicationServiceWebhookView.as_view(), name='communication_service_webhook'),
    
    # Integration management
    path('providers/', views.IntegrationProviderViewSet.as_view({'get': 'list', 'post': 'create'}), name='providers'),
    path('providers/<uuid:pk>/', views.IntegrationProviderViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='provider_detail'),
    
    # Webhook events
    path('events/', views.WebhookEventViewSet.as_view({'get': 'list'}), name='webhook_events'),
    path('events/<uuid:pk>/', views.WebhookEventViewSet.as_view({'get': 'retrieve'}), name='webhook_event_detail'),
    path('events/<uuid:pk>/retry/', views.WebhookEventViewSet.as_view({'post': 'retry'}), name='webhook_event_retry'),
    
    # External API calls
    path('api-calls/', views.ExternalAPICallViewSet.as_view({'get': 'list'}), name='api_calls'),
    path('api-calls/<uuid:pk>/', views.ExternalAPICallViewSet.as_view({'get': 'retrieve'}), name='api_call_detail'),
    
    # Health monitoring
    path('health/', views.IntegrationHealthViewSet.as_view({'get': 'list'}), name='integration_health'),
    path('health/<uuid:pk>/', views.IntegrationHealthViewSet.as_view({'get': 'retrieve'}), name='integration_health_detail'),
    
    # Circuit breaker status
    path('circuit-breaker/status/', views.CircuitBreakerStatusView.as_view(), name='circuit_breaker_status'),
]
