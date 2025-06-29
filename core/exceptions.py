from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from django.http import Http404
from django.utils.translation import gettext_lazy as _


class SaaSPlatformException(Exception):
    """Base exception for SaaS platform."""
    
    def __init__(self, message=None, code=None, details=None):
        self.message = message or "An error occurred"
        self.code = code or "UNKNOWN_ERROR"
        self.details = details or {}
        super().__init__(self.message)


class TenantNotFoundError(SaaSPlatformException):
    """Raised when a tenant is not found."""
    
    def __init__(self, tenant_id=None, domain=None):
        message = "Tenant not found"
        if tenant_id:
            message = f"Tenant with ID {tenant_id} not found"
        elif domain:
            message = f"Tenant with domain {domain} not found"
        
        super().__init__(message=message, code="TENANT_NOT_FOUND")


class TenantAccessDeniedError(SaaSPlatformException):
    """Raised when access to tenant is denied."""
    
    def __init__(self, tenant_id=None):
        message = "Access to tenant denied"
        if tenant_id:
            message = f"Access to tenant {tenant_id} denied"
        
        super().__init__(message=message, code="TENANT_ACCESS_DENIED")


class UserNotFoundError(SaaSPlatformException):
    """Raised when a user is not found."""
    
    def __init__(self, user_id=None, email=None):
        message = "User not found"
        if user_id:
            message = f"User with ID {user_id} not found"
        elif email:
            message = f"User with email {email} not found"
        
        super().__init__(message=message, code="USER_NOT_FOUND")


class IntegrationError(SaaSPlatformException):
    """Raised when an integration fails."""
    
    def __init__(self, provider=None, operation=None, details=None):
        message = "Integration error occurred"
        if provider and operation:
            message = f"Integration error in {provider} during {operation}"
        elif provider:
            message = f"Integration error in {provider}"
        
        super().__init__(message=message, code="INTEGRATION_ERROR", details=details)


class WebhookProcessingError(SaaSPlatformException):
    """Raised when webhook processing fails."""
    
    def __init__(self, event_type=None, event_id=None, details=None):
        message = "Webhook processing error"
        if event_type and event_id:
            message = f"Error processing webhook {event_type} with ID {event_id}"
        elif event_type:
            message = f"Error processing webhook {event_type}"
        
        super().__init__(message=message, code="WEBHOOK_PROCESSING_ERROR", details=details)


class CircuitBreakerOpenError(SaaSPlatformException):
    """Raised when circuit breaker is open."""
    
    def __init__(self, provider=None):
        message = "Circuit breaker is open"
        if provider:
            message = f"Circuit breaker is open for {provider}"
        
        super().__init__(message=message, code="CIRCUIT_BREAKER_OPEN")


class RateLimitExceededError(SaaSPlatformException):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, limit=None, window=None):
        message = "Rate limit exceeded"
        if limit and window:
            message = f"Rate limit exceeded: {limit} requests per {window}"
        
        super().__init__(message=message, code="RATE_LIMIT_EXCEEDED")


class InvalidTokenError(SaaSPlatformException):
    """Raised when a token is invalid."""
    
    def __init__(self, token_type=None):
        message = "Invalid token"
        if token_type:
            message = f"Invalid {token_type} token"
        
        super().__init__(message=message, code="INVALID_TOKEN")


class PermissionDeniedError(SaaSPlatformException):
    """Raised when permission is denied."""
    
    def __init__(self, resource=None, action=None):
        message = "Permission denied"
        if resource and action:
            message = f"Permission denied: cannot {action} {resource}"
        elif resource:
            message = f"Permission denied for {resource}"
        
        super().__init__(message=message, code="PERMISSION_DENIED")


class ValidationError(SaaSPlatformException):
    """Raised when data validation fails."""
    
    def __init__(self, field_errors=None):
        message = "Validation error"
        super().__init__(message=message, code="VALIDATION_ERROR", details=field_errors)


class ConfigurationError(SaaSPlatformException):
    """Raised when there's a configuration error."""
    
    def __init__(self, component=None, setting=None):
        message = "Configuration error"
        if component and setting:
            message = f"Configuration error in {component}: {setting}"
        elif component:
            message = f"Configuration error in {component}"
        
        super().__init__(message=message, code="CONFIGURATION_ERROR")


def custom_exception_handler(exc, context):
    """Custom exception handler for REST framework."""
    
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Customize the error response
        if isinstance(exc, SaaSPlatformException):
            response.data = {
                'error': {
                    'code': exc.code,
                    'message': exc.message,
                    'details': exc.details
                }
            }
        else:
            # Handle other exceptions
            response.data = {
                'error': {
                    'code': 'UNKNOWN_ERROR',
                    'message': str(exc),
                    'details': {}
                }
            }
    
    return response


def handle_tenant_not_found(request, tenant_id=None, domain=None):
    """Handle tenant not found scenarios."""
    if tenant_id:
        raise TenantNotFoundError(tenant_id=tenant_id)
    elif domain:
        raise TenantNotFoundError(domain=domain)
    else:
        raise TenantNotFoundError()


def handle_user_not_found(request, user_id=None, email=None):
    """Handle user not found scenarios."""
    if user_id:
        raise UserNotFoundError(user_id=user_id)
    elif email:
        raise UserNotFoundError(email=email)
    else:
        raise UserNotFoundError()


def handle_integration_error(provider, operation, details=None):
    """Handle integration errors."""
    raise IntegrationError(provider=provider, operation=operation, details=details)


def handle_webhook_error(event_type, event_id, details=None):
    """Handle webhook processing errors."""
    raise WebhookProcessingError(event_type=event_type, event_id=event_id, details=details)
