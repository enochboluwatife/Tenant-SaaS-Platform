"""
Essential tests for the Multi-Tenant SaaS Platform.
Covers core functionality required for the assessment.
"""

import os
import django
from django.conf import settings
settings.ROOT_URLCONF = 'config.urls'
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.tenants.models import Tenant, TenantUser
from apps.integrations.models import IntegrationProvider, WebhookEvent

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

User = get_user_model()

class EssentialFunctionalityTestCase(TestCase):
    """Test essential platform functionality."""

    def setUp(self):
        self.test_password = os.environ.get('TEST_PASSWORD', 'test_password_123')

    def test_tenant_creation(self):
        """Test tenant model."""
        tenant = Tenant.objects.create(
            name="Test Company",
            domain="testcompany.com"
        )
        self.assertEqual(tenant.name, "Test Company")
        self.assertEqual(tenant.domain, "testcompany.com")
        self.assertTrue(tenant.is_active)

    def test_user_creation(self):
        """Test user model."""
        tenant = Tenant.objects.create(
            name="Test Company",
            domain="testcompany.com"
        )
        user = TenantUser.objects.create_user(
            username="test@example.com",
            email="test@example.com",
            password=self.test_password,
            tenant=tenant
        )
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.tenant, tenant)

    def test_tenant_user_relationship(self):
        """Test tenant-user relationship."""
        tenant = Tenant.objects.create(
            name="Test Company",
            domain="testcompany.com"
        )
        user = TenantUser.objects.create_user(
            username="test@example.com",
            email="test@example.com",
            password=self.test_password,
            tenant=tenant
        )
        
        # Test that user belongs to tenant
        self.assertEqual(user.tenant, tenant)
        
        # Test that tenant has user
        self.assertIn(user, tenant.users.all())

    def test_multi_tenant_isolation(self):
        """Test multi-tenant data isolation."""
        # Create two tenants
        tenant1 = Tenant.objects.create(
            name="Company A",
            domain="companya.com"
        )
        tenant2 = Tenant.objects.create(
            name="Company B", 
            domain="companyb.com"
        )
        
        # Create users for each tenant
        user1 = TenantUser.objects.create_user(
            username="user1@companya.com",
            email="user1@companya.com",
            password=self.test_password,
            tenant=tenant1
        )
        user2 = TenantUser.objects.create_user(
            username="user2@companyb.com",
            email="user2@companyb.com",
            password=self.test_password,
            tenant=tenant2
        )
        
        # Verify isolation
        self.assertEqual(user1.tenant, tenant1)
        self.assertEqual(user2.tenant, tenant2)
        self.assertNotEqual(user1.tenant, user2.tenant)
        
        # Verify tenant user lists
        self.assertIn(user1, tenant1.users.all())
        self.assertIn(user2, tenant2.users.all())
        self.assertNotIn(user1, tenant2.users.all())
        self.assertNotIn(user2, tenant1.users.all())

class EssentialAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.test_password = os.environ.get('TEST_PASSWORD', 'test_password_123')
        
        # Create test tenant
        self.tenant = Tenant.objects.create(
            name="Test Company",
            domain="testcompany.com",
            is_active=True
        )
        
        # Create test user
        self.user = User.objects.create_user(
            username="test@example.com",
            email="test@example.com",
            password=self.test_password,
            first_name="Test",
            last_name="User",
            tenant=self.tenant
        )
        
        # Create superuser for admin tests
        self.admin_user = User.objects.create_superuser(
            username="admin@example.com",
            email="admin@example.com",
            password=self.test_password,
            first_name="Admin",
            last_name="User"
        )

    def test_user_registration(self):
        """Test user registration endpoint"""
        url = reverse('auth:register')
        data = {
            "email": "newuser@example.com",
            "password": self.test_password,
            "password_confirm": self.test_password,
            "first_name": "New",
            "last_name": "User",
            "tenant_name": "New Company",
            "tenant_domain": "newcompany.com"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
        # Check that user has tenant info
        self.assertIn('tenant', response.data['user'])

    def test_user_login(self):
        """Test user login endpoint"""
        url = reverse('auth:login')
        data = {
            "email": "test@example.com",
            "password": self.test_password
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Login endpoint returns user info, not tokens
        self.assertIn('user', response.data)
        self.assertIn('message', response.data)

    def test_jwt_token_obtain(self):
        """Test JWT token obtain endpoint"""
        url = reverse('auth:token_obtain_pair')
        data = {
            "username": "test@example.com",
            "password": self.test_password
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_protected_endpoint_with_auth(self):
        """Test accessing protected endpoint with authentication"""
        # Get JWT token
        token_url = reverse('auth:token_obtain_pair')
        token_data = {
            "username": "test@example.com",
            "password": self.test_password
        }
        token_response = self.client.post(token_url, token_data, format='json')
        token = token_response.data['access']
        
        # Test protected endpoint
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        profile_url = reverse('auth:profile')
        response = self.client.get(profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health_check(self):
        """Test health check endpoint"""
        url = reverse('health')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.content.decode(), 'OK')

    def test_integration_providers_list(self):
        """Test integration providers endpoint (admin only)"""
        # Login as admin
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('integrations:providers')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_audit_logging(self):
        """Test that audit logging works"""
        # Create an integration provider to trigger audit log
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('integrations:providers')
        data = {
            "name": "user_service",
            "webhook_url": "https://webhook.testprovider.com",
            "api_base_url": "https://api.testprovider.com",
            "auth_type": "api_key",
            "secret_key": "test_key_123",
            "config": {},
            "rate_limit_per_minute": 100,
            "burst_limit": 20,
            "max_retries": 3,
            "backoff_multiplier": 2.0,
            "max_backoff_seconds": 300,
            "is_active": True
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that audit log was created
        from apps.audit.models import AuditLog
        
        # The middleware logs with action='CREATE' and resource_type='API'
        audit_logs = AuditLog.objects.filter(
            action='CREATE',
            resource_type='API'
        )
        self.assertTrue(audit_logs.exists()) 