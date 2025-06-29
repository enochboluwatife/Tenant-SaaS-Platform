from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Tenant, TenantUser
from .serializers import (
    TenantSerializer, TenantUserSerializer, TenantUserCreateSerializer,
    TenantSummarySerializer
)
from .permissions import IsTenantAdmin, IsTenantUser
from apps.audit.models import AuditLog


class TenantViewSet(viewsets.ModelViewSet):
    """ViewSet for tenant management."""
    
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['plan', 'is_active']
    search_fields = ['name', 'domain']
    ordering_fields = ['name', 'created_at', 'employee_count']
    ordering = ['name']
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        if self.request.user.is_superuser:
            return Tenant.objects.all()
        elif hasattr(self.request.user, 'tenant'):
            return Tenant.objects.filter(id=self.request.user.tenant.id)
        return Tenant.objects.none()
    
    @action(detail=True, methods=['get'])
    def users(self, request, pk=None):
        """Get users for a specific tenant."""
        tenant = self.get_object()
        users = tenant.users.all()
        serializer = TenantUserSerializer(users, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        """Get tenant summary information."""
        tenant = self.get_object()
        serializer = TenantSummarySerializer(tenant)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a tenant."""
        tenant = self.get_object()
        tenant.is_active = False
        tenant.save()
        
        # Log the action
        AuditLog.log_action(
            user=request.user,
            tenant=tenant,
            action='UPDATE',
            resource_type='Tenant',
            resource_id=str(tenant.id),
            old_values={'is_active': True},
            new_values={'is_active': False},
            request=request
        )
        
        return Response({'status': 'tenant deactivated'})
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a tenant."""
        tenant = self.get_object()
        tenant.is_active = True
        tenant.save()
        
        # Log the action
        AuditLog.log_action(
            user=request.user,
            tenant=tenant,
            action='UPDATE',
            resource_type='Tenant',
            resource_id=str(tenant.id),
            old_values={'is_active': False},
            new_values={'is_active': True},
            request=request
        )
        
        return Response({'status': 'tenant activated'})


class TenantUserViewSet(viewsets.ModelViewSet):
    """ViewSet for tenant user management."""
    
    queryset = TenantUser.objects.all()
    serializer_class = TenantUserSerializer
    permission_classes = [IsTenantUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['department', 'is_active']
    search_fields = ['email', 'first_name', 'last_name']
    ordering_fields = ['email', 'first_name', 'last_name', 'created_at']
    ordering = ['first_name', 'last_name']
    
    def get_queryset(self):
        """Filter users by tenant."""
        if self.request.user.is_superuser:
            return TenantUser.objects.all()
        elif hasattr(self.request.user, 'tenant'):
            return TenantUser.objects.filter(tenant=self.request.user.tenant)
        return TenantUser.objects.none()
    
    def get_serializer_class(self):
        """Use different serializers for different actions."""
        if self.action == 'create':
            return TenantUserCreateSerializer
        return TenantUserSerializer
    
    def perform_create(self, serializer):
        """Create user with audit logging."""
        user = serializer.save()
        
        # Log the action
        AuditLog.log_action(
            user=self.request.user,
            tenant=user.tenant,
            action='CREATE',
            resource_type='TenantUser',
            resource_id=str(user.id),
            new_values={
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'department': user.department,
            },
            request=self.request
        )
    
    def perform_update(self, serializer):
        """Update user with audit logging."""
        old_values = {
            'email': serializer.instance.email,
            'first_name': serializer.instance.first_name,
            'last_name': serializer.instance.last_name,
            'department': serializer.instance.department,
            'title': serializer.instance.title,
        }
        
        user = serializer.save()
        
        # Log the action
        AuditLog.log_action(
            user=self.request.user,
            tenant=user.tenant,
            action='UPDATE',
            resource_type='TenantUser',
            resource_id=str(user.id),
            old_values=old_values,
            new_values={
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'department': user.department,
                'title': user.title,
            },
            request=self.request
        )
    
    def perform_destroy(self, instance):
        """Delete user with audit logging."""
        # Log the action before deletion
        AuditLog.log_action(
            user=self.request.user,
            tenant=instance.tenant,
            action='DELETE',
            resource_type='TenantUser',
            resource_id=str(instance.id),
            old_values={
                'email': instance.email,
                'first_name': instance.first_name,
                'last_name': instance.last_name,
            },
            request=self.request
        )
        
        instance.delete()
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a user."""
        user = self.get_object()
        user.is_active = False
        user.save()
        
        # Log the action
        AuditLog.log_action(
            user=request.user,
            tenant=user.tenant,
            action='UPDATE',
            resource_type='TenantUser',
            resource_id=str(user.id),
            old_values={'is_active': True},
            new_values={'is_active': False},
            request=request
        )
        
        return Response({'status': 'user deactivated'})
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a user."""
        user = self.get_object()
        user.is_active = True
        user.save()
        
        # Log the action
        AuditLog.log_action(
            user=request.user,
            tenant=user.tenant,
            action='UPDATE',
            resource_type='TenantUser',
            resource_id=str(user.id),
            old_values={'is_active': False},
            new_values={'is_active': True},
            request=request
        )
        
        return Response({'status': 'user activated'})
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's profile."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
