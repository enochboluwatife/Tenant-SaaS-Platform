from django.utils import timezone
from .models import WebhookEvent, IntegrationProvider
from apps.tenants.models import TenantUser, Tenant
import logging

logger = logging.getLogger(__name__)


def handle_user_service_webhook(event_data, request):
    """Handle webhook events from user management service."""
    
    # Create webhook event record
    provider = IntegrationProvider.objects.get(name='user_service')
    webhook_event = WebhookEvent.objects.create(
        provider=provider,
        event_type=event_data.get('event_type'),
        event_id=event_data.get('event_id'),
        organization_id=event_data.get('organization_id'),
        data=event_data.get('data', {}),
        metadata=event_data.get('metadata', {}),
        source_ip=request.META.get('REMOTE_ADDR'),
        headers=dict(request.headers)
    )
    
    try:
        webhook_event.mark_processing()
        
        event_type = event_data.get('event_type')
        data = event_data.get('data', {})
        
        if event_type == 'user.created':
            result = _handle_user_created(data, webhook_event)
        elif event_type == 'user.updated':
            result = _handle_user_updated(data, webhook_event)
        elif event_type == 'user.deleted':
            result = _handle_user_deleted(data, webhook_event)
        elif event_type == 'user.activated':
            result = _handle_user_activated(data, webhook_event)
        elif event_type == 'user.deactivated':
            result = _handle_user_deactivated(data, webhook_event)
        else:
            raise ValueError(f"Unknown event type: {event_type}")
        
        webhook_event.mark_completed()
        return {'status': 'success', 'message': f'Processed {event_type}'}
        
    except Exception as e:
        logger.error(f"Error processing user service webhook: {e}")
        webhook_event.mark_failed(str(e))
        
        # Schedule retry if appropriate
        if webhook_event.schedule_retry():
            return {'status': 'retry_scheduled', 'message': 'Event scheduled for retry'}
        else:
            return {'status': 'failed', 'message': str(e)}


def _handle_user_created(data, webhook_event):
    """Handle user.created event."""
    # Find tenant by organization ID
    tenant = Tenant.objects.filter(domain=data.get('organization_domain')).first()
    if not tenant:
        raise ValueError(f"Tenant not found for domain: {data.get('organization_domain')}")
    
    # Create or update user
    user, created = TenantUser.objects.get_or_create(
        email=data.get('email'),
        tenant=tenant,
        defaults={
            'first_name': data.get('first_name', ''),
            'last_name': data.get('last_name', ''),
            'department': data.get('department', ''),
            'title': data.get('title', ''),
            'sso_attributes': data.get('sso_attributes', {}),
        }
    )
    
    if not created:
        # Update existing user
        user.first_name = data.get('first_name', user.first_name)
        user.last_name = data.get('last_name', user.last_name)
        user.department = data.get('department', user.department)
        user.title = data.get('title', user.title)
        user.sso_attributes.update(data.get('sso_attributes', {}))
        user.save()
    
    return {'user_id': str(user.id), 'created': created}


def _handle_user_updated(data, webhook_event):
    """Handle user.updated event."""
    # Find user by external ID or email
    user = TenantUser.objects.filter(
        sso_attributes__external_user_id=data.get('user_id')
    ).first()
    
    if not user:
        raise ValueError(f"User not found: {data.get('user_id')}")
    
    # Update user fields
    changes = data.get('changes', {})
    for field, value in changes.items():
        if hasattr(user, field):
            setattr(user, field, value)
    
    # Update SSO attributes
    if 'sso_attributes' in data:
        user.sso_attributes.update(data['sso_attributes'])
    
    user.save()
    
    return {'user_id': str(user.id), 'updated_fields': list(changes.keys())}


def _handle_user_deleted(data, webhook_event):
    """Handle user.deleted event."""
    # Find user by external ID or email
    user = TenantUser.objects.filter(
        sso_attributes__external_user_id=data.get('user_id')
    ).first()
    
    if not user:
        raise ValueError(f"User not found: {data.get('user_id')}")
    
    # Deactivate user instead of deleting (soft delete)
    user.is_active = False
    user.save()
    
    return {'user_id': str(user.id), 'deactivated': True}


def _handle_user_activated(data, webhook_event):
    """Handle user.activated event."""
    user = TenantUser.objects.filter(
        sso_attributes__external_user_id=data.get('user_id')
    ).first()
    
    if not user:
        raise ValueError(f"User not found: {data.get('user_id')}")
    
    user.is_active = True
    user.save()
    
    return {'user_id': str(user.id), 'activated': True}


def _handle_user_deactivated(data, webhook_event):
    """Handle user.deactivated event."""
    user = TenantUser.objects.filter(
        sso_attributes__external_user_id=data.get('user_id')
    ).first()
    
    if not user:
        raise ValueError(f"User not found: {data.get('user_id')}")
    
    user.is_active = False
    user.save()
    
    return {'user_id': str(user.id), 'deactivated': True}


def handle_payment_service_webhook(event_data, request):
    """Handle webhook events from payment service."""
    
    # Create webhook event record
    provider = IntegrationProvider.objects.get(name='payment_service')
    webhook_event = WebhookEvent.objects.create(
        provider=provider,
        event_type=event_data.get('event_type'),
        event_id=event_data.get('event_id'),
        organization_id=event_data.get('organization_id'),
        data=event_data.get('data', {}),
        metadata=event_data.get('metadata', {}),
        source_ip=request.META.get('REMOTE_ADDR'),
        headers=dict(request.headers)
    )
    
    try:
        webhook_event.mark_processing()
        
        event_type = event_data.get('event_type')
        data = event_data.get('data', {})
        
        if event_type == 'subscription.created':
            result = _handle_subscription_created(data, webhook_event)
        elif event_type == 'subscription.updated':
            result = _handle_subscription_updated(data, webhook_event)
        elif event_type == 'subscription.canceled':
            result = _handle_subscription_canceled(data, webhook_event)
        elif event_type == 'payment.succeeded':
            result = _handle_payment_succeeded(data, webhook_event)
        elif event_type == 'payment.failed':
            result = _handle_payment_failed(data, webhook_event)
        else:
            raise ValueError(f"Unknown event type: {event_type}")
        
        webhook_event.mark_completed()
        return {'status': 'success', 'message': f'Processed {event_type}'}
        
    except Exception as e:
        logger.error(f"Error processing payment service webhook: {e}")
        webhook_event.mark_failed(str(e))
        
        if webhook_event.schedule_retry():
            return {'status': 'retry_scheduled', 'message': 'Event scheduled for retry'}
        else:
            return {'status': 'failed', 'message': str(e)}


def _handle_subscription_created(data, webhook_event):
    """Handle subscription.created event."""
    # Find tenant by customer ID
    tenant = Tenant.objects.filter(domain=data.get('customer_domain')).first()
    if not tenant:
        raise ValueError(f"Tenant not found for customer: {data.get('customer_id')}")
    
    # Update tenant subscription info
    tenant.plan = data.get('plan', tenant.plan)
    # Add subscription fields to tenant model as needed
    
    return {'tenant_id': str(tenant.id), 'subscription_id': data.get('subscription_id')}


def _handle_subscription_updated(data, webhook_event):
    """Handle subscription.updated event."""
    tenant = Tenant.objects.filter(domain=data.get('customer_domain')).first()
    if not tenant:
        raise ValueError(f"Tenant not found for customer: {data.get('customer_id')}")
    
    # Update subscription details
    tenant.plan = data.get('plan', tenant.plan)
    
    return {'tenant_id': str(tenant.id), 'subscription_id': data.get('subscription_id')}


def _handle_subscription_canceled(data, webhook_event):
    """Handle subscription.canceled event."""
    tenant = Tenant.objects.filter(domain=data.get('customer_domain')).first()
    if not tenant:
        raise ValueError(f"Tenant not found for customer: {data.get('customer_id')}")
    
    # Handle subscription cancellation
    tenant.is_active = False
    
    return {'tenant_id': str(tenant.id), 'subscription_id': data.get('subscription_id')}


def _handle_payment_succeeded(data, webhook_event):
    """Handle payment.succeeded event."""
    # Process successful payment
    return {'payment_id': data.get('payment_id'), 'amount': data.get('amount')}


def _handle_payment_failed(data, webhook_event):
    """Handle payment.failed event."""
    # Process failed payment
    return {'payment_id': data.get('payment_id'), 'failure_reason': data.get('failure_reason')}


def handle_communication_service_webhook(event_data, request):
    """Handle webhook events from communication service."""
    
    # Create webhook event record
    provider = IntegrationProvider.objects.get(name='communication_service')
    webhook_event = WebhookEvent.objects.create(
        provider=provider,
        event_type=event_data.get('event_type'),
        event_id=event_data.get('event_id'),
        organization_id=event_data.get('organization_id'),
        data=event_data.get('data', {}),
        metadata=event_data.get('metadata', {}),
        source_ip=request.META.get('REMOTE_ADDR'),
        headers=dict(request.headers)
    )
    
    try:
        webhook_event.mark_processing()
        
        event_type = event_data.get('event_type')
        data = event_data.get('data', {})
        
        if event_type == 'message.delivered':
            result = _handle_message_delivered(data, webhook_event)
        elif event_type == 'message.bounced':
            result = _handle_message_bounced(data, webhook_event)
        elif event_type == 'message.clicked':
            result = _handle_message_clicked(data, webhook_event)
        elif event_type == 'message.opened':
            result = _handle_message_opened(data, webhook_event)
        else:
            raise ValueError(f"Unknown event type: {event_type}")
        
        webhook_event.mark_completed()
        return {'status': 'success', 'message': f'Processed {event_type}'}
        
    except Exception as e:
        logger.error(f"Error processing communication service webhook: {e}")
        webhook_event.mark_failed(str(e))
        
        if webhook_event.schedule_retry():
            return {'status': 'retry_scheduled', 'message': 'Event scheduled for retry'}
        else:
            return {'status': 'failed', 'message': str(e)}


def _handle_message_delivered(data, webhook_event):
    """Handle message.delivered event."""
    # Process message delivery confirmation
    return {'message_id': data.get('message_id'), 'status': 'delivered'}


def _handle_message_bounced(data, webhook_event):
    """Handle message.bounced event."""
    # Process message bounce
    return {'message_id': data.get('message_id'), 'bounce_reason': data.get('bounce_reason')}


def _handle_message_clicked(data, webhook_event):
    """Handle message.clicked event."""
    # Process message click
    return {'message_id': data.get('message_id'), 'clicked_at': data.get('clicked_at')}


def _handle_message_opened(data, webhook_event):
    """Handle message.opened event."""
    # Process message open
    return {'message_id': data.get('message_id'), 'opened_at': data.get('opened_at')}
