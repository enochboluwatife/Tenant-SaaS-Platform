from functools import wraps
from django.utils.decorators import method_decorator
from .models import AuditLog


def audit_action(action_type, resource_type='', resource_id_field='id'):
    """Decorator to automatically log actions."""
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get request from args (assuming it's the first argument after self)
            request = None
            if len(args) > 1:
                request = args[1]  # For class methods
            elif len(args) > 0 and hasattr(args[0], 'request'):
                request = args[0].request  # For view methods
            
            # Execute the function
            result = func(*args, **kwargs)
            
            # Log the action if we have a request
            if request and hasattr(request, 'user'):
                try:
                    # Extract resource ID if available
                    resource_id = ''
                    if resource_id_field in kwargs:
                        resource_id = str(kwargs[resource_id_field])
                    elif hasattr(result, resource_id_field):
                        resource_id = str(getattr(result, resource_id_field))
                    
                    AuditLog.log_action(
                        user=request.user,
                        tenant=getattr(request, 'tenant', None),
                        action=action_type,
                        resource_type=resource_type,
                        resource_id=resource_id,
                        request=request
                    )
                except Exception as e:
                    # Don't let audit logging break the application
                    print(f"Audit logging error: {e}")
            
            return result
        return wrapper
    return decorator


def audit_view_action(action_type, resource_type=''):
    """Decorator for view actions."""
    return method_decorator(audit_action(action_type, resource_type), name='dispatch')
