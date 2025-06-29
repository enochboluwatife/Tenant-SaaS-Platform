#!/usr/bin/env python3
"""
Comprehensive endpoint testing script for Multi-Tenant SaaS Platform.
Run this script to test all endpoints and verify they work correctly.
"""

import requests
import json
import sys
import time
from typing import Dict, Any, Optional
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

# Get test password from environment or use default
TEST_PASSWORD = os.environ.get('TEST_PASSWORD', 'test_password_123')

class EndpointTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.access_token = None
        self.refresh_token = None
        self.test_user = None
        self.test_tenant = None
        self.test_results = []
        
    def print_result(self, endpoint: str, status: str, details: str = ""):
        """Print test result with formatting."""
        if status == "PASS":
            print(f"✅ {endpoint:<50} {status}")
        elif status == "FAIL":
            print(f"❌ {endpoint:<50} {status}")
        else:
            print(f"⚠️  {endpoint:<50} {status}")
        
        if details:
            print(f"   {details}")
    
    def log_test(self, endpoint, method, status_code, success, details=""):
        """Log test results"""
        result = {
            "timestamp": datetime.now().isoformat(),
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "success": success,
            "details": details
        }
        self.test_results.append(result)
        
        status_icon = "✅" if success else "❌"
        print(f"{status_icon} {method} {endpoint} - {status_code} {details}")
    
    def test_health_endpoint(self) -> bool:
        """Test health check endpoint."""
        try:
            response = self.session.get(f"{self.base_url}/health/")
            if response.status_code == 200 and response.text.strip() == "OK":
                self.print_result("/health/", "PASS")
                self.log_test("/health/", "GET", response.status_code, True)
                return True
            else:
                self.print_result("/health/", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                self.log_test("/health/", "GET", response.status_code, False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.print_result("/health/", "FAIL", f"Error: {str(e)}")
            self.log_test("/health/", "GET", 0, False, f"Error: {str(e)}")
            return False
    
    def test_user_registration(self) -> bool:
        """Test user registration endpoint."""
        try:
            data = {
                "email": f"testuser_{int(time.time())}@example.com",
                "password": TEST_PASSWORD,
                "password_confirm": TEST_PASSWORD,
                "first_name": "Test",
                "last_name": "User",
                "tenant_name": f"Test Company {int(time.time())}",
                "tenant_domain": f"testcompany{int(time.time())}.com"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/auth/register/",
                json=data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 201:
                result = response.json()
                self.test_user = result.get('user', {})
                self.test_tenant = self.test_user.get('tenant', {})
                self.print_result("/api/auth/register/", "PASS")
                self.log_test("/api/auth/register/", "POST", response.status_code, True)
                return True
            else:
                self.print_result("/api/auth/register/", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                self.log_test("/api/auth/register/", "POST", response.status_code, False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.print_result("/api/auth/register/", "FAIL", f"Error: {str(e)}")
            self.log_test("/api/auth/register/", "POST", 0, False, f"Error: {str(e)}")
            return False
    
    def test_user_login(self) -> bool:
        """Test user login endpoint."""
        if not self.test_user:
            self.print_result("/api/auth/login/", "SKIP", "No test user available")
            self.log_test("/api/auth/login/", "POST", 0, False, "No test user available")
            return False
            
        try:
            data = {
                "email": self.test_user['email'],
                "password": TEST_PASSWORD
            }
            
            response = self.session.post(
                f"{self.base_url}/api/auth/login/",
                json=data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                self.print_result("/api/auth/login/", "PASS")
                self.access_token = result.get('access')
                self.refresh_token = result.get('refresh')
                self.session.headers.update({
                    'Authorization': f'Bearer {self.access_token}'
                })
                self.log_test("/api/auth/login/", "POST", response.status_code, True)
                return True
            else:
                self.print_result("/api/auth/login/", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                self.log_test("/api/auth/login/", "POST", response.status_code, False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.print_result("/api/auth/login/", "FAIL", f"Error: {str(e)}")
            self.log_test("/api/auth/login/", "POST", 0, False, f"Error: {str(e)}")
            return False
    
    def test_jwt_token_obtain(self) -> bool:
        """Test JWT token obtain endpoint."""
        if not self.test_user:
            self.print_result("/api/auth/token/", "SKIP", "No test user available")
            self.log_test("/api/auth/token/", "POST", 0, False, "No test user available")
            return False
            
        try:
            data = {
                "email": self.test_user['email'],  # JWT expects username field
                "password": TEST_PASSWORD
            }
            
            response = self.session.post(
                f"{self.base_url}/api/auth/token/",
                json=data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                self.access_token = result.get('access')
                self.refresh_token = result.get('refresh')
                self.session.headers.update({
                    'Authorization': f'Bearer {self.access_token}'
                })
                self.print_result("/api/auth/token/", "PASS")
                self.log_test("/api/auth/token/", "POST", response.status_code, True)
                return True
            else:
                self.print_result("/api/auth/token/", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                self.log_test("/api/auth/token/", "POST", response.status_code, False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.print_result("/api/auth/token/", "FAIL", f"Error: {str(e)}")
            self.log_test("/api/auth/token/", "POST", 0, False, f"Error: {str(e)}")
            return False
    
    def test_protected_endpoints(self) -> Dict[str, bool]:
        """Test protected endpoints with JWT token."""
        if not self.access_token:
            self.print_result("Protected endpoints", "SKIP", "No access token available")
            self.log_test("Protected endpoints", "GET", 0, False, "No access token")
            return {}
        
        results = {}
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # Test user profile
        try:
            response = self.session.get(f"{self.base_url}/api/auth/profile/", headers=headers)
            if response.status_code == 200:
                self.print_result("/api/auth/profile/", "PASS")
                self.log_test("/api/auth/profile/", "GET", response.status_code, True)
                results['profile'] = True
            else:
                self.print_result("/api/auth/profile/", "FAIL", f"Status: {response.status_code}")
                self.log_test("/api/auth/profile/", "GET", response.status_code, False, f"Status: {response.status_code}")
                results['profile'] = False
        except Exception as e:
            self.print_result("/api/auth/profile/", "FAIL", f"Error: {str(e)}")
            self.log_test("/api/auth/profile/", "GET", 0, False, f"Error: {str(e)}")
            results['profile'] = False
        
        # Test users list
        try:
            response = self.session.get(f"{self.base_url}/api/users/", headers=headers)
            if response.status_code == 200:
                self.print_result("/api/users/", "PASS")
                self.log_test("/api/users/", "GET", response.status_code, True)
                results['users'] = True
            else:
                self.print_result("/api/users/", "FAIL", f"Status: {response.status_code}")
                self.log_test("/api/users/", "GET", response.status_code, False, f"Status: {response.status_code}")
                results['users'] = False
        except Exception as e:
            self.print_result("/api/users/", "FAIL", f"Error: {str(e)}")
            self.log_test("/api/users/", "GET", 0, False, f"Error: {str(e)}")
            results['users'] = False
        
        # Test tenants (may be forbidden for regular users)
        try:
            response = self.session.get(f"{self.base_url}/api/tenants/", headers=headers)
            if response.status_code in [200, 403]:  # 403 is expected for non-admin users
                status = "PASS" if response.status_code == 200 else "EXPECTED_FORBIDDEN"
                self.print_result("/api/tenants/", status, f"Status: {response.status_code}")
                self.log_test("/api/tenants/", "GET", response.status_code, response.status_code in [200, 403])
                results['tenants'] = True
            else:
                self.print_result("/api/tenants/", "FAIL", f"Status: {response.status_code}")
                self.log_test("/api/tenants/", "GET", response.status_code, False, f"Status: {response.status_code}")
                results['tenants'] = False
        except Exception as e:
            self.print_result("/api/tenants/", "FAIL", f"Error: {str(e)}")
            self.log_test("/api/tenants/", "GET", 0, False, f"Error: {str(e)}")
            results['tenants'] = False
        
        # Test integration endpoints
        integration_endpoints = [
            "/api/integrations/providers/",
            "/api/integrations/events/",
            "/api/integrations/health/"
        ]
        
        for endpoint in integration_endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}", headers=headers)
                if response.status_code in [200, 403]:  # 403 is expected for non-admin users
                    status = "PASS" if response.status_code == 200 else "EXPECTED_FORBIDDEN"
                    self.print_result(endpoint, status, f"Status: {response.status_code}")
                    self.log_test(endpoint, "GET", response.status_code, response.status_code in [200, 403])
                    results[endpoint] = True
                else:
                    self.print_result(endpoint, "FAIL", f"Status: {response.status_code}")
                    self.log_test(endpoint, "GET", response.status_code, False, f"Status: {response.status_code}")
                    results[endpoint] = False
            except Exception as e:
                self.print_result(endpoint, "FAIL", f"Error: {str(e)}")
                self.log_test(endpoint, "GET", 0, False, f"Error: {str(e)}")
                results[endpoint] = False
        
        return results
    
    def test_webhook_endpoints(self) -> Dict[str, bool]:
        """Test webhook endpoints (should work without authentication)."""
        results = {}
        
        webhook_data = {
            "event_type": "user.created",
            "event_id": f"evt_{int(time.time())}",
            "data": {
                "user_id": "123",
                "email": "webhook@example.com"
            }
        }
        
        webhook_endpoints = [
            "/api/integrations/webhooks/user-service/",
            "/api/integrations/webhooks/payment-service/"
        ]
        
        for endpoint in webhook_endpoints:
            try:
                response = self.session.post(
                    f"{self.base_url}{endpoint}",
                    json=webhook_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code in [200, 201, 400]:  # 400 might be expected for invalid data
                    status = "PASS" if response.status_code in [200, 201] else "EXPECTED_BAD_REQUEST"
                    self.print_result(endpoint, status, f"Status: {response.status_code}")
                    self.log_test(endpoint, "POST", response.status_code, response.status_code in [200, 201])
                    results[endpoint] = True
                else:
                    self.print_result(endpoint, "FAIL", f"Status: {response.status_code}")
                    self.log_test(endpoint, "POST", response.status_code, False, f"Status: {response.status_code}")
                    results[endpoint] = False
            except Exception as e:
                self.print_result(endpoint, "FAIL", f"Error: {str(e)}")
                self.log_test(endpoint, "POST", 0, False, f"Error: {str(e)}")
                results[endpoint] = False
        
        return results
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all endpoint tests and return results."""
        print("🚀 Starting Comprehensive Endpoint Testing")
        print("=" * 60)
        
        results = {
            'health': False,
            'registration': False,
            'login': False,
            'jwt_token': False,
            'protected_endpoints': {},
            'webhook_endpoints': {}
        }
        
        # Test health endpoint
        results['health'] = self.test_health_endpoint()
        
        # Test user registration
        results['registration'] = self.test_user_registration()
        
        # Test user login
        results['login'] = self.test_user_login()
        
        # Test JWT token obtain
        results['jwt_token'] = self.test_jwt_token_obtain()
        
        # Test protected endpoints
        results['protected_endpoints'] = self.test_protected_endpoints()
        
        # Test webhook endpoints
        results['webhook_endpoints'] = self.test_webhook_endpoints()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = 1 + 1 + 1 + 1 + len(results['protected_endpoints']) + len(results['webhook_endpoints'])
        passed_tests = sum([
            results['health'],
            results['registration'],
            results['login'],
            results['jwt_token'],
            sum(results['protected_endpoints'].values()),
            sum(results['webhook_endpoints'].values())
        ])
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Save results to file
        with open('test_results.json', 'w') as f:
            json.dump(self.test_results, f, indent=2)
        print(f"\n📄 Detailed results saved to: test_results.json")
        
        return results

def main():
    """Main function to run the endpoint tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test all endpoints of the Multi-Tenant SaaS Platform')
    parser.add_argument('--base-url', default='http://localhost:8000', 
                       help='Base URL of the API (default: http://localhost:8000)')
    parser.add_argument('--output', help='Output file for results (JSON format)')
    
    args = parser.parse_args()
    
    tester = EndpointTester(args.base_url)
    results = tester.run_all_tests()
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to: {args.output}")
    
    # Exit with error code if any critical tests failed
    critical_tests = ['health', 'registration', 'login']
    failed_critical = any(not results[test] for test in critical_tests)
    
    if failed_critical:
        print("\n❌ Critical tests failed!")
        sys.exit(1)
    else:
        print("\n✅ All critical tests passed!")
        sys.exit(0)

if __name__ == "__main__":
    main() 