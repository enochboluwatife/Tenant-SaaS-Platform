import requests
import logging
from typing import Dict, Any, Optional
from django.conf import settings
from .circuit_breaker import CircuitBreaker, circuit_breaker
from .models import ExternalAPICall, IntegrationProvider
from apps.audit.models import AuditLog

logger = logging.getLogger(__name__)


class ExternalAPIClient:
    """Base class for external API clients with circuit breaker and retry logic."""
    
    def __init__(self, provider_name: str, base_url: str, api_key: str = None):
        self.provider_name = provider_name
        self.base_url = base_url
        self.api_key = api_key
        self.circuit_breaker = CircuitBreaker(provider_name)
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            })
    
    @circuit_breaker(provider_name='external_api', threshold=3, timeout=60)
    def make_request(self, method: str, endpoint: str, data: Dict = None, 
                    params: Dict = None, user=None, correlation_id: str = None) -> Dict[str, Any]:
        """Make an API request with circuit breaker protection."""
        
        # Create API call record
        api_call = ExternalAPICall.objects.create(
            provider=self._get_provider(),
            endpoint=f"{self.base_url}{endpoint}",
            method=method.upper(),
            request_data=data or {},
            correlation_id=correlation_id,
            user=user
        )
        
        try:
            api_call.mark_in_progress()
            
            # Make the request
            response = self.session.request(
                method=method,
                url=f"{self.base_url}{endpoint}",
                json=data,
                params=params,
                timeout=30
            )
            
            response.raise_for_status()
            response_data = response.json()
            
            # Mark as completed
            api_call.mark_completed(response_data, response.status_code)
            
            return response_data
            
        except Exception as e:
            # Mark as failed
            api_call.mark_failed(str(e))
            logger.error(f"API call failed: {e}")
            raise
    
    def _get_provider(self) -> Optional[IntegrationProvider]:
        """Get the integration provider."""
        try:
            return IntegrationProvider.objects.get(name=self.provider_name)
        except IntegrationProvider.DoesNotExist:
            return None


class UserServiceClient(ExternalAPIClient):
    """Client for user management service."""
    
    def __init__(self):
        super().__init__(
            provider_name='user_service',
            base_url='https://api.userservice.com/v1',
            api_key='test_api_key'
        )
    
    def create_user(self, user_data: Dict[str, Any], user=None) -> Dict[str, Any]:
        """Create a user."""
        return self.make_request('POST', '/users', data=user_data, user=user)
    
    def update_user(self, user_id: str, user_data: Dict[str, Any], user=None) -> Dict[str, Any]:
        """Update a user."""
        return self.make_request('PUT', f'/users/{user_id}', data=user_data, user=user)
    
    def delete_user(self, user_id: str, user=None) -> Dict[str, Any]:
        """Delete a user."""
        return self.make_request('DELETE', f'/users/{user_id}', user=user)


class PaymentServiceClient(ExternalAPIClient):
    """Client for payment service."""
    
    def __init__(self):
        super().__init__(
            provider_name='payment_service',
            base_url='https://api.payments.com/v2',
            api_key='test_payment_key'
        )
    
    def create_subscription(self, subscription_data: Dict[str, Any], user=None) -> Dict[str, Any]:
        """Create a subscription."""
        return self.make_request('POST', '/subscriptions', data=subscription_data, user=user)
    
    def process_payment(self, payment_data: Dict[str, Any], user=None) -> Dict[str, Any]:
        """Process a payment."""
        return self.make_request('POST', '/payments', data=payment_data, user=user)


class CommunicationServiceClient(ExternalAPIClient):
    """Client for communication service."""
    
    def __init__(self):
        super().__init__(
            provider_name='communication_service',
            base_url='https://api.emailservice.com/v1',
            api_key='test_email_key'
        )
    
    def send_email(self, email_data: Dict[str, Any], user=None) -> Dict[str, Any]:
        """Send an email."""
        return self.make_request('POST', '/emails', data=email_data, user=user)
    
    def send_notification(self, notification_data: Dict[str, Any], user=None) -> Dict[str, Any]:
        """Send a notification."""
        return self.make_request('POST', '/notifications', data=notification_data, user=user)


# Factory functions
def get_user_service_client() -> UserServiceClient:
    """Get user service client."""
    return UserServiceClient()


def get_payment_service_client() -> PaymentServiceClient:
    """Get payment service client."""
    return PaymentServiceClient()


def get_communication_service_client() -> CommunicationServiceClient:
    """Get communication service client."""
    return CommunicationServiceClient()
