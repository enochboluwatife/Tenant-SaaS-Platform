from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from .models import AuditLog
import json


class AuditMiddleware(MiddlewareMixin):
    """Middleware to automatically log API calls and user actions."""
    
    def process_request(self, request):
        """Process incoming request and log if needed."""
        # Skip logging for certain paths
        if self._should_skip_logging(request.path):
            return None
        
        # Store request info for later use in process_response
        request._audit_info = {
            'path': request.path,
            'method': request.method,
            'user': getattr(request, 'user', None),
            'tenant': getattr(request, 'tenant', None),
        }
    
    def process_response(self, request, response):
        """Process response and log the API call."""
        # Skip if we didn't store audit info
        if not hasattr(request, '_audit_info'):
            return response
        
        # Skip logging for certain paths
        if self._should_skip_logging(request.path):
            return response
        
        # Only log API calls (JSON responses)
        if not self._is_api_call(request, response):
            return response
        
        try:
            # Determine action based on HTTP method
            action_map = {
                'GET': 'API_CALL',
                'POST': 'CREATE',
                'PUT': 'UPDATE',
                'PATCH': 'UPDATE',
                'DELETE': 'DELETE',
            }
            
            action = action_map.get(request.method, 'API_CALL')
            
            # Log the API call
            AuditLog.log_action(
                user=request._audit_info['user'],
                tenant=request._audit_info['tenant'],
                action=action,
                resource_type='API',
                resource_id=request.path,
                request=request,
                correlation_id=request.headers.get('X-Correlation-ID', ''),
            )
            
        except Exception as e:
            # Don't let audit logging break the application
            print(f"Audit logging error: {e}")
        
        return response
    
    def _should_skip_logging(self, path):
        """Check if logging should be skipped for this path."""
        skip_paths = [
            '/admin/',
            '/static/',
            '/media/',
            '/health/',
            '/metrics/',
        ]
        
        return any(path.startswith(skip_path) for skip_path in skip_paths)
    
    def _is_api_call(self, request, response):
        """Check if this is an API call that should be logged."""
        # Check if it's a JSON response
        content_type = response.get('Content-Type', '')
        if 'application/json' in content_type:
            return True
        
        # Check if it's an API endpoint
        api_paths = ['/api/', '/webhooks/']
        if any(request.path.startswith(api_path) for api_path in api_paths):
            return True
        
        return False
