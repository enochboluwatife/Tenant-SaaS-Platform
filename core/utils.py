import uuid
import hashlib
import secrets
from typing import Dict, Any, Optional
from django.utils import timezone
from django.core.cache import cache


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


def generate_api_key() -> str:
    """Generate a secure API key."""
    return secrets.token_urlsafe(32)


def generate_correlation_id() -> str:
    """Generate a correlation ID for request tracking."""
    return f"corr_{int(timezone.now().timestamp())}_{secrets.token_hex(4)}"


def hash_sensitive_data(data: str) -> str:
    """Hash sensitive data for storage."""
    return hashlib.sha256(data.encode()).hexdigest()


def mask_email(email: str) -> str:
    """Mask an email address for display."""
    if '@' not in email:
        return email
    
    username, domain = email.split('@')
    if len(username) <= 2:
        masked_username = username
    else:
        masked_username = username[0] + '*' * (len(username) - 2) + username[-1]
    
    return f"{masked_username}@{domain}"


def mask_phone(phone: str) -> str:
    """Mask a phone number for display."""
    if len(phone) <= 4:
        return phone
    
    return '*' * (len(phone) - 4) + phone[-4:]


def get_client_ip(request) -> str:
    """Extract client IP from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request) -> str:
    """Extract user agent from request."""
    return request.META.get('HTTP_USER_AGENT', '')


def cache_with_timeout(key: str, data: Any, timeout: int = 300) -> None:
    """Cache data with timeout."""
    cache.set(key, data, timeout)


def get_cached_data(key: str) -> Optional[Any]:
    """Get cached data."""
    return cache.get(key)


def invalidate_cache(key: str) -> None:
    """Invalidate cached data."""
    cache.delete(key)


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"


def validate_json_schema(data: Dict, schema: Dict) -> bool:
    """Basic JSON schema validation."""
    # This is a simplified validation - in production, use a proper JSON schema library
    for field, field_schema in schema.items():
        if field_schema.get('required', False) and field not in data:
            return False
        
        if field in data:
            field_type = field_schema.get('type')
            if field_type == 'string' and not isinstance(data[field], str):
                return False
            elif field_type == 'integer' and not isinstance(data[field], int):
                return False
            elif field_type == 'boolean' and not isinstance(data[field], bool):
                return False
            elif field_type == 'array' and not isinstance(data[field], list):
                return False
            elif field_type == 'object' and not isinstance(data[field], dict):
                return False
    
    return True


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage."""
    import re
    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:255-len(ext)-1] + '.' + ext if ext else name[:255]
    return filename


def generate_secure_password(length: int = 12) -> str:
    """Generate a secure password."""
    import string
    characters = string.ascii_letters + string.digits + string.punctuation
    # Ensure at least one of each type
    password = [
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.digits),
        secrets.choice(string.punctuation)
    ]
    # Fill the rest randomly
    password.extend(secrets.choice(characters) for _ in range(length - 4))
    # Shuffle the password
    password_list = list(password)
    secrets.SystemRandom().shuffle(password_list)
    return ''.join(password_list)


def is_valid_uuid(uuid_string: str) -> bool:
    """Check if a string is a valid UUID."""
    try:
        uuid.UUID(uuid_string)
        return True
    except ValueError:
        return False


def truncate_text(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """Truncate text to specified length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def parse_duration(duration_str: str) -> int:
    """Parse duration string to seconds."""
    import re
    
    # Parse formats like "1h", "30m", "2h30m", "1d"
    total_seconds = 0
    
    # Days
    days_match = re.search(r'(\d+)d', duration_str)
    if days_match:
        total_seconds += int(days_match.group(1)) * 86400
    
    # Hours
    hours_match = re.search(r'(\d+)h', duration_str)
    if hours_match:
        total_seconds += int(hours_match.group(1)) * 3600
    
    # Minutes
    minutes_match = re.search(r'(\d+)m', duration_str)
    if minutes_match:
        total_seconds += int(minutes_match.group(1)) * 60
    
    # Seconds
    seconds_match = re.search(r'(\d+)s', duration_str)
    if seconds_match:
        total_seconds += int(seconds_match.group(1))
    
    return total_seconds


def format_duration(seconds: int) -> str:
    """Format duration in seconds to human readable format."""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes}m{remaining_seconds}s" if remaining_seconds else f"{minutes}m"
    elif seconds < 86400:
        hours = seconds // 3600
        remaining_minutes = (seconds % 3600) // 60
        return f"{hours}h{remaining_minutes}m" if remaining_minutes else f"{hours}h"
    else:
        days = seconds // 86400
        remaining_hours = (seconds % 86400) // 3600
        return f"{days}d{remaining_hours}h" if remaining_hours else f"{days}d"
