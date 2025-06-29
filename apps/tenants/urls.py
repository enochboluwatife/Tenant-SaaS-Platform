"""
URL patterns for the tenants app.
"""

from django.urls import path
from . import views

app_name = 'tenants'

urlpatterns = [
    # Tenant management
    path('', views.TenantListView.as_view(), name='tenant-list'),
    path('<int:pk>/', views.TenantDetailView.as_view(), name='tenant-detail'),
    path('create/', views.TenantCreateView.as_view(), name='tenant-create'),
    path('<int:pk>/update/', views.TenantUpdateView.as_view(), name='tenant-update'),
    path('<int:pk>/delete/', views.TenantDeleteView.as_view(), name='tenant-delete'),
    
    # Tenant user management
    path('<int:tenant_id>/users/', views.TenantUserListView.as_view(), name='tenant-user-list'),
    path('<int:tenant_id>/users/<int:pk>/', views.TenantUserDetailView.as_view(), name='tenant-user-detail'),
    path('<int:tenant_id>/users/create/', views.TenantUserCreateView.as_view(), name='tenant-user-create'),
    path('<int:tenant_id>/users/<int:pk>/update/', views.TenantUserUpdateView.as_view(), name='tenant-user-update'),
    path('<int:tenant_id>/users/<int:pk>/delete/', views.TenantUserDeleteView.as_view(), name='tenant-user-delete'),
    
    # Tenant settings
    path('<int:pk>/settings/', views.TenantSettingsView.as_view(), name='tenant-settings'),
    path('<int:pk>/billing/', views.TenantBillingView.as_view(), name='tenant-billing'),
    path('<int:pk>/integrations/', views.TenantIntegrationsView.as_view(), name='tenant-integrations'),
]
