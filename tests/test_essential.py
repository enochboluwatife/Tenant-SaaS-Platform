"""
Essential tests for the Multi-Tenant SaaS Platform.
Covers core functionality required for the assessment.
"""

from django.test import TestCase
from apps.tenants.models import Tenant, TenantUser


class EssentialFunctionalityTestCase(TestCase):
    """Test essential platform functionality."""

    def test_tenant_creation(self):
        """Test tenant model."""
        tenant = Tenant.objects.create(
            name="Test Company",
            domain="testcompany.com",
            is_active=True
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
            password="testpass123",
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
            password="testpass123",
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
            password="pass123",
            tenant=tenant1
        )
        user2 = TenantUser.objects.create_user(
            username="user2@companyb.com",
            email="user2@companyb.com",
            password="pass123",
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