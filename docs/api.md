# API Documentation

## Overview

This document provides comprehensive API documentation for the Multi-Tenant SaaS Platform with External Integrations.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://api.yourapp.com`

## Authentication

### JWT Authentication

The API uses JWT (JSON Web Tokens) for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your_access_token>
```

### Getting Tokens

#### Login
```http
POST /api/auth/token/
Content-Type: application/json

{
    "username": "user@example.com",
    "password": "your_password"
}
```

**Response:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": 1,
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "role": "admin"
    }
}
```

#### Refresh Token
```http
POST /api/auth/token/refresh/
Content-Type: application/json

{
    "refresh": "your_refresh_token"
}
```

## API Endpoints

### Health Check

#### Get System Health
```http
GET /health/
```

**Response:**
```json
"OK"
```

### Authentication Endpoints

#### Register User
```http
POST /api/auth/register/
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "secure_password",
    "password_confirm": "secure_password",
    "first_name": "John",
    "last_name": "Doe",
    "tenant_name": "My Company",
    "tenant_domain": "mycompany.com"
}
```

#### Login
```http
POST /api/auth/login/
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "secure_password"
}
```

#### Logout
```http
POST /api/auth/logout/
Authorization: Bearer <token>
```

#### Get User Profile
```http
GET /api/auth/profile/
Authorization: Bearer <token>
```

### Tenant Management

#### List Tenants (Admin Only)
```http
GET /api/tenants/
Authorization: Bearer <token>
```

**Response:**
```json
{
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "name": "My Company",
            "domain": "mycompany.com",
            "is_active": true,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    ]
}
```

#### Get Tenant Details
```http
GET /api/tenants/{id}/
Authorization: Bearer <token>
```

#### Create Tenant
```http
POST /api/tenants/
Authorization: Bearer <token>
Content-Type: application/json

{
    "name": "New Company",
    "domain": "newcompany.com",
    "settings": {
        "timezone": "UTC",
        "language": "en"
    }
}
```

#### Update Tenant
```http
PUT /api/tenants/{id}/
Authorization: Bearer <token>
Content-Type: application/json

{
    "name": "Updated Company Name",
    "settings": {
        "timezone": "America/New_York"
    }
}
```

#### Delete Tenant
```http
DELETE /api/tenants/{id}/
Authorization: Bearer <token>
```

### User Management

#### List Users
```http
GET /api/users/
Authorization: Bearer <token>
```

**Response:**
```json
{
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "email": "admin@company.com",
            "first_name": "Admin",
            "last_name": "User",
            "role": "admin",
            "is_active": true,
            "last_login": "2024-01-01T12:00:00Z"
        }
    ]
}
```

#### Get User Details
```http
GET /api/users/{id}/
Authorization: Bearer <token>
```

#### Create User
```http
POST /api/users/
Authorization: Bearer <token>
Content-Type: application/json

{
    "email": "newuser@company.com",
    "password": "secure_password",
    "first_name": "New",
    "last_name": "User",
    "role": "user"
}
```

#### Update User
```http
PUT /api/users/{id}/
Authorization: Bearer <token>
Content-Type: application/json

{
    "first_name": "Updated",
    "role": "admin"
}
```

#### Delete User
```http
DELETE /api/users/{id}/
Authorization: Bearer <token>
```

### Integration Management

#### List Integration Providers
```http
GET /api/integrations/providers/
Authorization: Bearer <token>
```

**Response:**
```json
{
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "name": "user_service",
            "webhook_url": "https://webhook.userservice.com",
            "api_base_url": "https://api.userservice.com",
            "auth_type": "api_key",
            "is_active": true,
            "created_at": "2024-01-01T00:00:00Z"
        }
    ]
}
```

#### Get Integration Provider Details
```http
GET /api/integrations/providers/{id}/
Authorization: Bearer <token>
```

#### Create Integration Provider
```http
POST /api/integrations/providers/
Authorization: Bearer <token>
Content-Type: application/json

{
    "name": "new_service",
    "webhook_url": "https://webhook.newservice.com",
    "api_base_url": "https://api.newservice.com",
    "auth_type": "oauth2",
    "secret_key": "your_secret_key"
}
```

#### List Webhook Events
```http
GET /api/integrations/events/
Authorization: Bearer <token>
```

**Response:**
```json
{
    "count": 5,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "event_type": "user.created",
            "event_id": "evt_123",
            "provider": "user_service",
            "status": "processed",
            "created_at": "2024-01-01T00:00:00Z"
        }
    ]
}
```

#### Get Integration Health
```http
GET /api/integrations/health/
Authorization: Bearer <token>
```

**Response:**
```json
{
    "status": "healthy",
    "providers": {
        "user_service": {
            "status": "healthy",
            "response_time": 150,
            "last_check": "2024-01-01T12:00:00Z"
        },
        "payment_service": {
            "status": "degraded",
            "response_time": 2000,
            "last_check": "2024-01-01T12:00:00Z"
        }
    }
}
```

### Webhook Endpoints

#### User Service Webhook
```http
POST /api/integrations/webhooks/user-service/
Content-Type: application/json

{
    "event_type": "user.created",
    "event_id": "evt_123",
    "data": {
        "user_id": "123",
        "email": "user@example.com",
        "name": "John Doe"
    }
}
```

#### Payment Service Webhook
```http
POST /api/integrations/webhooks/payment-service/
Content-Type: application/json

{
    "event_type": "payment.succeeded",
    "event_id": "evt_456",
    "data": {
        "payment_id": "pay_123",
        "amount": 1000,
        "currency": "usd"
    }
}
```

### Audit Logging

#### List Audit Logs
```http
GET /api/audit/logs/
Authorization: Bearer <token>
```

**Query Parameters:**
- `action`: Filter by action type
- `resource_type`: Filter by resource type
- `user_id`: Filter by user
- `date_from`: Start date (ISO format)
- `date_to`: End date (ISO format)

**Response:**
```json
{
    "count": 100,
    "next": "http://localhost:8000/api/audit/logs/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "user": {
                "id": 1,
                "email": "admin@company.com"
            },
            "action": "create",
            "resource_type": "user",
            "resource_id": "123",
            "old_values": {},
            "new_values": {
                "email": "user@example.com",
                "first_name": "John"
            },
            "ip_address": "192.168.1.1",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    ]
}
```

## Error Handling

### Error Response Format

All API errors follow a consistent format:

```json
{
    "error": "error_type",
    "message": "Human-readable error message",
    "details": {
        "field_name": ["Specific field error"]
    },
    "timestamp": "2024-01-01T00:00:00Z"
}
```

### Common HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

### Rate Limiting

The API implements rate limiting:

- **Anonymous users**: 100 requests per hour
- **Authenticated users**: 1000 requests per hour
- **Per-tenant limits**: Additional tenant-specific limits

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## Pagination

List endpoints support pagination with the following parameters:

- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 100)

**Response format:**
```json
{
    "count": 100,
    "next": "http://localhost:8000/api/users/?page=2",
    "previous": null,
    "results": [...]
}
```

## Filtering and Searching

Many endpoints support filtering and searching:

### Filtering
```
GET /api/users/?role=admin&is_active=true
```

### Searching
```
GET /api/users/?search=john
```

### Ordering
```
GET /api/users/?ordering=-created_at
```

## Webhooks

### Webhook Security

Webhooks are secured using:
- **Signature verification**: HMAC-SHA256 signatures
- **IP whitelisting**: Allowed IP addresses
- **Rate limiting**: Per-provider limits

### Webhook Retry Logic

Failed webhooks are retried with exponential backoff:
- Initial delay: 60 seconds
- Maximum retries: 3
- Maximum delay: 300 seconds

### Webhook Events

Supported event types:
- `user.created`
- `user.updated`
- `user.deleted`
- `payment.succeeded`
- `payment.failed`
- `subscription.created`
- `subscription.updated`

## SDKs and Libraries

### Python SDK
```python
from saas_platform import Client

client = Client(api_key="your_api_key")
users = client.users.list()
```

### JavaScript SDK
```javascript
import { Client } from '@saas-platform/sdk';

const client = new Client({ apiKey: 'your_api_key' });
const users = await client.users.list();
```

## Support

For API support:
- **Documentation**: https://docs.yourapp.com
- **Email**: api-support@yourapp.com
- **Status Page**: https://status.yourapp.com
