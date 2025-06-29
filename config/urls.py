"""
URL configuration for saas_platform project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.tenants.views import TenantViewSet, TenantUserViewSet
from apps.authentication.views import (
    CustomTokenObtainPairView, CustomTokenRefreshView,
    LoginView, LogoutView, RegisterView, PasswordChangeView,
    PasswordResetView, PasswordResetConfirmView, UserProfileView, revoke_token
)
from django.http import HttpResponse

# Create router for API endpoints
router = DefaultRouter()
router.register(r'tenants', TenantViewSet)
router.register(r'users', TenantUserViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/', include(router.urls)),
    
    # Authentication endpoints (stub for namespace)
    path('api/auth/', include(('apps.authentication.urls', 'auth'), namespace='auth')),
    
    # Integrations endpoints with namespace
    path('api/integrations/', include(('apps.integrations.urls', 'integrations'), namespace='integrations')),
    
    # Health check endpoint
    path('health/', lambda request: HttpResponse('OK'), name='health'),
]

# Add Django REST framework auth URLs
from django.conf import settings
if settings.DEBUG:
    # Commented out due to coreapi dependency issues
    # from rest_framework.documentation import include_docs_urls
    # urlpatterns += [
    #     path('api/docs/', include_docs_urls(title='SaaS Platform API')),
    # ]
    pass
