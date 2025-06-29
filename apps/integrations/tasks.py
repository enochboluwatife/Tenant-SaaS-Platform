from celery import shared_task
from django.utils import timezone
from .models import WebhookEvent, IntegrationProvider
from .webhook_handlers import (
    handle_user_service_webhook, handle_payment_service_webhook, 
    handle_communication_service_webhook
)
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_webhook_event(self, event_id: str):
    """Process a webhook event asynchronously."""
    try:
        event = WebhookEvent.objects.get(id=event_id)
        
        # Route to appropriate handler based on provider
        if event.provider.name == 'user_service':
            handle_user_service_webhook(event.data, None)
        elif event.provider.name == 'payment_service':
            handle_payment_service_webhook(event.data, None)
        elif event.provider.name == 'communication_service':
            handle_communication_service_webhook(event.data, None)
        else:
            logger.error(f"Unknown provider: {event.provider.name}")
            event.mark_failed(f"Unknown provider: {event.provider.name}")
            
    except WebhookEvent.DoesNotExist:
        logger.error(f"Webhook event not found: {event_id}")
    except Exception as e:
        logger.error(f"Error processing webhook event {event_id}: {e}")
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            countdown = 2 ** self.request.retries  # Exponential backoff
            raise self.retry(countdown=countdown, exc=e)
        else:
            # Mark as failed after max retries
            try:
                event = WebhookEvent.objects.get(id=event_id)
                event.mark_failed(f"Max retries exceeded: {str(e)}")
            except WebhookEvent.DoesNotExist:
                pass


@shared_task
def retry_failed_webhooks():
    """Retry failed webhook events that are due for retry."""
    now = timezone.now()
    failed_events = WebhookEvent.objects.filter(
        status='retry',
        next_retry_at__lte=now
    )
    
    for event in failed_events:
        process_webhook_event.delay(str(event.id))
    
    logger.info(f"Scheduled {failed_events.count()} webhook events for retry")


@shared_task
def cleanup_old_webhook_events():
    """Clean up old webhook events to prevent database bloat."""
    from datetime import timedelta
    
    # Delete events older than 30 days
    cutoff_date = timezone.now() - timedelta(days=30)
    deleted_count = WebhookEvent.objects.filter(
        received_at__lt=cutoff_date,
        status__in=['completed', 'failed']
    ).delete()[0]
    
    logger.info(f"Cleaned up {deleted_count} old webhook events")


@shared_task
def sync_integration_providers():
    """Sync integration provider configurations."""
    providers = IntegrationProvider.objects.filter(is_active=True)
    
    for provider in providers:
        try:
            # Update provider health status
            from .models import IntegrationHealth
            health, created = IntegrationHealth.objects.get_or_create(
                provider=provider,
                defaults={'is_healthy': True}
            )
            
            if not created:
                health.last_check_at = timezone.now()
                health.save()
                
        except Exception as e:
            logger.error(f"Error syncing provider {provider.name}: {e}")


@shared_task
def send_bulk_notifications(notification_data: dict, user_ids: list):
    """Send bulk notifications to multiple users."""
    from apps.tenants.models import TenantUser
    from .external_apis import get_communication_service_client
    
    client = get_communication_service_client()
    
    for user_id in user_ids:
        try:
            user = TenantUser.objects.get(id=user_id)
            
            # Add user-specific data
            user_notification_data = notification_data.copy()
            user_notification_data['recipient'] = user.email
            user_notification_data['variables'] = {
                'user_name': f"{user.first_name} {user.last_name}",
                'tenant_name': user.tenant.name,
                **notification_data.get('variables', {})
            }
            
            # Send notification
            client.send_notification(user_notification_data, user)
            
        except TenantUser.DoesNotExist:
            logger.error(f"User not found: {user_id}")
        except Exception as e:
            logger.error(f"Error sending notification to user {user_id}: {e}")


@shared_task
def sync_users_with_external_service(tenant_id: str):
    """Sync users with external user management service."""
    from apps.tenants.models import Tenant, TenantUser
    from .external_apis import get_user_service_client
    
    try:
        tenant = Tenant.objects.get(id=tenant_id)
        client = get_user_service_client()
        
        # Get all active users for the tenant
        users = TenantUser.objects.filter(tenant=tenant, is_active=True)
        
        for user in users:
            try:
                # Sync user data with external service
                user_data = {
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'department': user.department,
                    'title': user.title,
                    'organization_id': str(tenant.id),
                    'organization_domain': tenant.domain
                }
                
                # Update or create user in external service
                client.update_user(str(user.id), user_data, user)
                
            except Exception as e:
                logger.error(f"Error syncing user {user.id}: {e}")
                
    except Tenant.DoesNotExist:
        logger.error(f"Tenant not found: {tenant_id}")
    except Exception as e:
        logger.error(f"Error syncing users for tenant {tenant_id}: {e}")


@shared_task
def process_payment_webhooks():
    """Process pending payment webhooks."""
    payment_events = WebhookEvent.objects.filter(
        provider__name='payment_service',
        status='pending'
    )
    
    for event in payment_events:
        process_webhook_event.delay(str(event.id))


@shared_task
def process_user_webhooks():
    """Process pending user webhooks."""
    user_events = WebhookEvent.objects.filter(
        provider__name='user_service',
        status='pending'
    )
    
    for event in user_events:
        process_webhook_event.delay(str(event.id))
