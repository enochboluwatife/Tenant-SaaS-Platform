from django.http import Http404
from django.conf import settings
from .models import Tenant


class TenantMiddleware:
    """Middleware to handle multi-tenancy by extracting tenant from request."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Extract tenant from request
        tenant = self.get_tenant_from_request(request)
        
        if tenant:
            request.tenant = tenant
        else:
            # For non-tenant specific routes (like auth endpoints)
            request.tenant = None
        
        response = self.get_response(request)
        return response
    
    def get_tenant_from_request(self, request):
        """Extract tenant from request headers, subdomain, or path."""
        
        # Method 1: From X-Tenant header (for API calls)
        tenant_id = request.headers.get('X-Tenant-ID')
        if tenant_id:
            try:
                return Tenant.objects.get(id=tenant_id, is_active=True)
            except Tenant.DoesNotExist:
                return None
        
        # Method 2: From subdomain
        host = request.get_host().split(':')[0]
        if '.' in host:
            subdomain = host.split('.')[0]
            if subdomain not in ['www', 'api', 'admin']:
                try:
                    return Tenant.objects.get(domain=subdomain, is_active=True)
                except Tenant.DoesNotExist:
                    return None
        
        # Method 3: From path prefix (e.g., /tenant/tenant-id/...)
        path_parts = request.path.strip('/').split('/')
        if len(path_parts) >= 2 and path_parts[0] == 'tenant':
            tenant_id = path_parts[1]
            try:
                return Tenant.objects.get(id=tenant_id, is_active=True)
            except (Tenant.DoesNotExist, ValueError):
                return None
        
        return None


class TenantDatabaseMiddleware:
    """Middleware to route database queries to tenant-specific database."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # This would be used for database-level tenant isolation
        # For now, we'll use application-level isolation
        response = self.get_response(request)
        return response
