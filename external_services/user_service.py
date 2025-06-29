import requests
import json
import logging
from typing import Dict, Any, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class UserManagementService:
    """Mock user management service for testing integrations."""
    
    def __init__(self, base_url: str = "https://api.userservice.com/v1", api_key: str = "test_api_key"):
        self.base_url = base_url
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
    
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user."""
        try:
            response = self.session.post(
                f"{self.base_url}/users",
                json=user_data
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating user: {e}")
            raise
    
    def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing user."""
        try:
            response = self.session.put(
                f"{self.base_url}/users/{user_id}",
                json=user_data
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error updating user: {e}")
            raise
    
    def delete_user(self, user_id: str) -> Dict[str, Any]:
        """Delete a user."""
        try:
            response = self.session.delete(f"{self.base_url}/users/{user_id}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error deleting user: {e}")
            raise
    
    def get_user(self, user_id: str) -> Dict[str, Any]:
        """Get user details."""
        try:
            response = self.session.get(f"{self.base_url}/users/{user_id}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting user: {e}")
            raise
    
    def list_users(self, organization_id: str, **params) -> Dict[str, Any]:
        """List users for an organization."""
        try:
            params['organization_id'] = organization_id
            response = self.session.get(f"{self.base_url}/users", params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error listing users: {e}")
            raise
    
    def activate_user(self, user_id: str) -> Dict[str, Any]:
        """Activate a user account."""
        try:
            response = self.session.post(f"{self.base_url}/users/{user_id}/activate")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error activating user: {e}")
            raise
    
    def deactivate_user(self, user_id: str) -> Dict[str, Any]:
        """Deactivate a user account."""
        try:
            response = self.session.post(f"{self.base_url}/users/{user_id}/deactivate")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error deactivating user: {e}")
            raise
    
    def sync_users(self, organization_id: str) -> Dict[str, Any]:
        """Sync users for an organization."""
        try:
            response = self.session.post(
                f"{self.base_url}/organizations/{organization_id}/sync"
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error syncing users: {e}")
            raise


class MockUserService:
    """Mock implementation for testing without external API calls."""
    
    def __init__(self):
        self.users = {}
        self.next_id = 1
    
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a mock user."""
        user_id = f"ext_user_{self.next_id}"
        self.next_id += 1
        
        user = {
            'id': user_id,
            'email': user_data.get('email'),
            'first_name': user_data.get('first_name', ''),
            'last_name': user_data.get('last_name', ''),
            'department': user_data.get('department', ''),
            'title': user_data.get('title', ''),
            'status': 'active',
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-01T00:00:00Z'
        }
        
        self.users[user_id] = user
        return user
    
    def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a mock user."""
        if user_id not in self.users:
            raise ValueError(f"User not found: {user_id}")
        
        user = self.users[user_id]
        user.update(user_data)
        user['updated_at'] = '2024-01-01T00:00:00Z'
        
        return user
    
    def delete_user(self, user_id: str) -> Dict[str, Any]:
        """Delete a mock user."""
        if user_id not in self.users:
            raise ValueError(f"User not found: {user_id}")
        
        user = self.users.pop(user_id)
        return {'id': user_id, 'deleted': True}
    
    def get_user(self, user_id: str) -> Dict[str, Any]:
        """Get a mock user."""
        if user_id not in self.users:
            raise ValueError(f"User not found: {user_id}")
        
        return self.users[user_id]
    
    def list_users(self, organization_id: str, **params) -> Dict[str, Any]:
        """List mock users."""
        users = list(self.users.values())
        return {
            'users': users,
            'total': len(users),
            'page': params.get('page', 1),
            'per_page': params.get('per_page', 20)
        }
    
    def activate_user(self, user_id: str) -> Dict[str, Any]:
        """Activate a mock user."""
        if user_id not in self.users:
            raise ValueError(f"User not found: {user_id}")
        
        self.users[user_id]['status'] = 'active'
        return self.users[user_id]
    
    def deactivate_user(self, user_id: str) -> Dict[str, Any]:
        """Deactivate a mock user."""
        if user_id not in self.users:
            raise ValueError(f"User not found: {user_id}")
        
        self.users[user_id]['status'] = 'inactive'
        return self.users[user_id]
    
    def sync_users(self, organization_id: str) -> Dict[str, Any]:
        """Sync mock users."""
        return {
            'organization_id': organization_id,
            'synced_users': len(self.users),
            'status': 'completed'
        }


# Factory function to get the appropriate service
def get_user_service(use_mock: bool = True) -> UserManagementService:
    """Get user service instance."""
    if use_mock:
        return MockUserService()
    else:
        return UserManagementService()
