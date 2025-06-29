from rest_framework import permissions


class IsTenantUser(permissions.BasePermission):
    """Permission to check if user belongs to the tenant."""
    
    def has_permission(self, request, view):
        """Check if user has permission to access tenant data."""
        # Superusers can access everything
        if request.user.is_superuser:
            return True
        
        # Check if user has a tenant
        if not hasattr(request.user, 'tenant'):
            return False
        
        # Check if user is active
        if not request.user.is_active:
            return False
        
        return True
    
    def has_object_permission(self, request, view, obj):
        """Check if user has permission to access specific object."""
        # Superusers can access everything
        if request.user.is_superuser:
            return True
        
        # Check if user has a tenant
        if not hasattr(request.user, 'tenant'):
            return False
        
        # Check if object belongs to user's tenant
        if hasattr(obj, 'tenant'):
            return obj.tenant == request.user.tenant
        
        # For user objects, check if it's the same user or same tenant
        if hasattr(obj, 'id'):
            if obj.id == request.user.id:
                return True
            if hasattr(obj, 'tenant'):
                return obj.tenant == request.user.tenant
        
        return False


class IsTenantAdmin(permissions.BasePermission):
    """Permission to check if user is a tenant admin."""
    
    def has_permission(self, request, view):
        """Check if user has admin permission."""
        # Superusers can access everything
        if request.user.is_superuser:
            return True
        
        # Check if user has a tenant
        if not hasattr(request.user, 'tenant'):
            return False
        
        # Check if user is active
        if not request.user.is_active:
            return False
        
        # Check if user is staff (admin)
        return request.user.is_staff
    
    def has_object_permission(self, request, view, obj):
        """Check if user has admin permission for specific object."""
        # Superusers can access everything
        if request.user.is_superuser:
            return True
        
        # Check if user has a tenant
        if not hasattr(request.user, 'tenant'):
            return False
        
        # Check if user is staff (admin)
        if not request.user.is_staff:
            return False
        
        # Check if object belongs to user's tenant
        if hasattr(obj, 'tenant'):
            return obj.tenant == request.user.tenant
        
        return False


class IsTenantOwner(permissions.BasePermission):
    """Permission to check if user is the tenant owner."""
    
    def has_permission(self, request, view):
        """Check if user has owner permission."""
        # Superusers can access everything
        if request.user.is_superuser:
            return True
        
        # Check if user has a tenant
        if not hasattr(request.user, 'tenant'):
            return False
        
        # Check if user is active
        if not request.user.is_active:
            return False
        
        # Check if user is the tenant owner (first user created)
        tenant = request.user.tenant
        first_user = tenant.users.order_by('created_at').first()
        return request.user == first_user
    
    def has_object_permission(self, request, view, obj):
        """Check if user has owner permission for specific object."""
        # Superusers can access everything
        if request.user.is_superuser:
            return True
        
        # Check if user has a tenant
        if not hasattr(request.user, 'tenant'):
            return False
        
        # Check if user is the tenant owner
        tenant = request.user.tenant
        first_user = tenant.users.order_by('created_at').first()
        if request.user != first_user:
            return False
        
        # Check if object belongs to user's tenant
        if hasattr(obj, 'tenant'):
            return obj.tenant == request.user.tenant
        
        return False


class IsSameTenant(permissions.BasePermission):
    """Permission to check if user and object belong to the same tenant."""
    
    def has_object_permission(self, request, view, obj):
        """Check if user and object belong to the same tenant."""
        # Superusers can access everything
        if request.user.is_superuser:
            return True
        
        # Check if user has a tenant
        if not hasattr(request.user, 'tenant'):
            return False
        
        # Check if object has a tenant
        if not hasattr(obj, 'tenant'):
            return False
        
        # Check if they belong to the same tenant
        return obj.tenant == request.user.tenant


class IsOwnerOrTenantAdmin(permissions.BasePermission):
    """Permission to check if user is the owner or a tenant admin."""
    
    def has_object_permission(self, request, view, obj):
        """Check if user is the owner or a tenant admin."""
        # Superusers can access everything
        if request.user.is_superuser:
            return True
        
        # Check if user has a tenant
        if not hasattr(request.user, 'tenant'):
            return False
        
        # Check if object belongs to user's tenant
        if hasattr(obj, 'tenant') and obj.tenant != request.user.tenant:
            return False
        
        # Check if user is the owner of the object
        if hasattr(obj, 'user') and obj.user == request.user:
            return True
        
        # Check if user is a tenant admin
        if request.user.is_staff:
            return True
        
        return False
