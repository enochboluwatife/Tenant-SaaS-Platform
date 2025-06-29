import requests
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from django.conf import settings

logger = logging.getLogger(__name__)


class PaymentService:
    """Mock payment service for testing integrations."""
    
    def __init__(self, base_url: str = "https://api.payments.com/v2", api_key: str = "test_payment_key"):
        self.base_url = base_url
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
    
    def create_subscription(self, subscription_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new subscription."""
        try:
            response = self.session.post(
                f"{self.base_url}/subscriptions",
                json=subscription_data
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating subscription: {e}")
            raise
    
    def update_subscription(self, subscription_id: str, subscription_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing subscription."""
        try:
            response = self.session.put(
                f"{self.base_url}/subscriptions/{subscription_id}",
                json=subscription_data
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error updating subscription: {e}")
            raise
    
    def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Cancel a subscription."""
        try:
            response = self.session.post(f"{self.base_url}/subscriptions/{subscription_id}/cancel")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error canceling subscription: {e}")
            raise
    
    def process_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a payment."""
        try:
            response = self.session.post(
                f"{self.base_url}/payments",
                json=payment_data
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error processing payment: {e}")
            raise
    
    def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Get subscription details."""
        try:
            response = self.session.get(f"{self.base_url}/subscriptions/{subscription_id}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting subscription: {e}")
            raise
    
    def list_subscriptions(self, customer_id: str, **params) -> Dict[str, Any]:
        """List subscriptions for a customer."""
        try:
            params['customer_id'] = customer_id
            response = self.session.get(f"{self.base_url}/subscriptions", params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error listing subscriptions: {e}")
            raise


class MockPaymentService:
    """Mock implementation for testing without external API calls."""
    
    def __init__(self):
        self.subscriptions = {}
        self.payments = {}
        self.next_subscription_id = 1
        self.next_payment_id = 1
    
    def create_subscription(self, subscription_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a mock subscription."""
        subscription_id = f"sub_{self.next_subscription_id}"
        self.next_subscription_id += 1
        
        subscription = {
            'id': subscription_id,
            'customer_id': subscription_data.get('customer_id'),
            'plan': subscription_data.get('plan', 'basic'),
            'status': 'active',
            'billing_cycle': subscription_data.get('billing_cycle', 'monthly'),
            'amount': subscription_data.get('amount', 29.99),
            'currency': subscription_data.get('currency', 'USD'),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'trial_end': None
        }
        
        self.subscriptions[subscription_id] = subscription
        return subscription
    
    def update_subscription(self, subscription_id: str, subscription_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a mock subscription."""
        if subscription_id not in self.subscriptions:
            raise ValueError(f"Subscription not found: {subscription_id}")
        
        subscription = self.subscriptions[subscription_id]
        subscription.update(subscription_data)
        subscription['updated_at'] = datetime.now().isoformat()
        
        return subscription
    
    def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Cancel a mock subscription."""
        if subscription_id not in self.subscriptions:
            raise ValueError(f"Subscription not found: {subscription_id}")
        
        subscription = self.subscriptions[subscription_id]
        subscription['status'] = 'canceled'
        subscription['canceled_at'] = datetime.now().isoformat()
        
        return subscription
    
    def process_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a mock payment."""
        payment_id = f"pay_{self.next_payment_id}"
        self.next_payment_id += 1
        
        # Simulate payment success/failure
        success = payment_data.get('amount', 0) > 0  # Simple success condition
        
        payment = {
            'id': payment_id,
            'subscription_id': payment_data.get('subscription_id'),
            'amount': payment_data.get('amount'),
            'currency': payment_data.get('currency', 'USD'),
            'status': 'succeeded' if success else 'failed',
            'created_at': datetime.now().isoformat(),
            'failure_reason': None if success else 'insufficient_funds'
        }
        
        self.payments[payment_id] = payment
        return payment
    
    def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Get a mock subscription."""
        if subscription_id not in self.subscriptions:
            raise ValueError(f"Subscription not found: {subscription_id}")
        
        return self.subscriptions[subscription_id]
    
    def list_subscriptions(self, customer_id: str, **params) -> Dict[str, Any]:
        """List mock subscriptions."""
        customer_subscriptions = [
            sub for sub in self.subscriptions.values()
            if sub['customer_id'] == customer_id
        ]
        
        return {
            'subscriptions': customer_subscriptions,
            'total': len(customer_subscriptions),
            'page': params.get('page', 1),
            'per_page': params.get('per_page', 20)
        }
    
    def create_invoice(self, subscription_id: str, amount: float) -> Dict[str, Any]:
        """Create a mock invoice."""
        invoice_id = f"inv_{len(self.payments) + 1}"
        
        invoice = {
            'id': invoice_id,
            'subscription_id': subscription_id,
            'amount': amount,
            'currency': 'USD',
            'status': 'pending',
            'due_date': (datetime.now() + timedelta(days=30)).isoformat(),
            'created_at': datetime.now().isoformat()
        }
        
        return invoice


# Factory function to get the appropriate service
def get_payment_service(use_mock: bool = True) -> PaymentService:
    """Get payment service instance."""
    if use_mock:
        return MockPaymentService()
    else:
        return PaymentService()
