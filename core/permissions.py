"""
Custom permission classes for the Multi-Tenant SaaS Platform.
"""

from rest_framework import permissions
from apps.tenants.models import TenantUser


class IsTenantUser(permissions.BasePermission):
    """
    Allow access only to authenticated users within the current tenant.
    """
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            hasattr(request, 'tenant') and
            request.tenant is not None
        )


class IsTenantAdmin(permissions.BasePermission):
    """
    Allow access only to tenant administrators.
    """
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            hasattr(request, 'tenant') and
            request.tenant is not None and
            hasattr(request.user, 'role') and
            request.user.role in ['admin', 'owner']
        )


class IsTenantOwner(permissions.BasePermission):
    """
    Allow access only to tenant owners.
    """
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            hasattr(request, 'tenant') and
            request.tenant is not None and
            hasattr(request.user, 'role') and
            request.user.role == 'owner'
        )


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only to the owner
        return obj.user == request.user


class IsTenantObjectOwner(permissions.BasePermission):
    """
    Object-level permission to only allow tenant owners to modify tenant objects.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for authenticated users in the same tenant
        if request.method in permissions.SAFE_METHODS:
            return (
                request.user.is_authenticated and
                hasattr(obj, 'tenant') and
                obj.tenant == request.tenant
            )
        
        # Write permissions only to tenant admins/owners
        return (
            request.user.is_authenticated and
            hasattr(obj, 'tenant') and
            obj.tenant == request.tenant and
            hasattr(request.user, 'role') and
            request.user.role in ['admin', 'owner']
        )


class HasIntegrationPermission(permissions.BasePermission):
    """
    Permission for integration-related operations.
    """
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            hasattr(request, 'tenant') and
            request.tenant is not None and
            hasattr(request.user, 'role') and
            request.user.role in ['admin', 'owner', 'developer']
        )
