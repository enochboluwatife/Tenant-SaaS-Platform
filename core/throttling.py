"""
Custom throttling classes for the Multi-Tenant SaaS Platform.
"""

from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from apps.tenants.models import Tenant


class TenantUserRateThrottle(UserRateThrottle):
    """
    Throttle based on user within a specific tenant.
    """
    scope = 'tenant_user'
    
    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            tenant = getattr(request, 'tenant', None)
            if tenant:
                return f"throttle_{self.scope}_{tenant.id}_{request.user.id}"
        return super().get_cache_key(request, view)


class TenantRateThrottle(UserRateThrottle):
    """
    Throttle based on tenant (organization level).
    """
    scope = 'tenant'
    
    def get_cache_key(self, request, view):
        tenant = getattr(request, 'tenant', None)
        if tenant:
            return f"throttle_{self.scope}_{tenant.id}"
        return super().get_cache_key(request, view)


class WebhookRateThrottle(AnonRateThrottle):
    """
    Throttle for webhook endpoints to prevent abuse.
    """
    scope = 'webhook'
    
    def get_cache_key(self, request, view):
        # Use IP address for webhook throttling
        return f"throttle_{self.scope}_{self.get_ident(request)}"


class IntegrationRateThrottle(UserRateThrottle):
    """
    Throttle for external integration calls.
    """
    scope = 'integration'
    
    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            tenant = getattr(request, 'tenant', None)
            if tenant:
                return f"throttle_{self.scope}_{tenant.id}_{request.user.id}"
        return super().get_cache_key(request, view)
