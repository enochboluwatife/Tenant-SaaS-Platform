from django.utils import timezone
from django.core.cache import cache
from .models import IntegrationHealth
import logging

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """Circuit breaker pattern implementation for external API calls."""
    
    def __init__(self, provider_name, threshold=5, timeout=60):
        """
        Initialize circuit breaker.
        
        Args:
            provider_name: Name of the external service provider
            threshold: Number of failures before opening circuit
            timeout: Time in seconds to wait before trying again
        """
        self.provider_name = provider_name
        self.threshold = threshold
        self.timeout = timeout
        self.cache_key = f"circuit_breaker:{provider_name}"
    
    @property
    def state(self):
        """Get current circuit breaker state."""
        cached_data = cache.get(self.cache_key)
        if not cached_data:
            return 'closed'
        return cached_data.get('state', 'closed')
    
    @property
    def failure_count(self):
        """Get current failure count."""
        cached_data = cache.get(self.cache_key)
        if not cached_data:
            return 0
        return cached_data.get('failure_count', 0)
    
    @property
    def last_failure_time(self):
        """Get last failure time."""
        cached_data = cache.get(self.cache_key)
        if not cached_data:
            return None
        return cached_data.get('last_failure_time')
    
    def call(self, func, *args, **kwargs):
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result if successful
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Original exception from function
        """
        if self.state == 'open':
            if self._should_attempt_reset():
                self._set_half_open()
            else:
                raise CircuitBreakerOpenError(f"Circuit breaker is open for {self.provider_name}")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self):
        """Check if enough time has passed to attempt reset."""
        cached_data = cache.get(self.cache_key)
        if not cached_data:
            return False
        
        last_failure = cached_data.get('last_failure_time')
        if not last_failure:
            return False
        
        # Convert string back to datetime if needed
        if isinstance(last_failure, str):
            from django.utils.dateparse import parse_datetime
            last_failure = parse_datetime(last_failure)
        
        if not last_failure:
            return False
        
        time_since_failure = (timezone.now() - last_failure).total_seconds()
        return time_since_failure >= self.timeout
    
    def _set_half_open(self):
        """Set circuit breaker to half-open state."""
        cache.set(self.cache_key, {
            'state': 'half_open',
            'failure_count': self.failure_count,
            'last_failure_time': self.last_failure_time
        }, self.timeout * 2)
        
        # Update health record
        self._update_health_record('half_open')
    
    def _on_success(self):
        """Handle successful call."""
        if self.state == 'half_open':
            # Reset circuit breaker on successful call
            cache.delete(self.cache_key)
            self._update_health_record('closed')
        elif self.state == 'closed':
            # Reset failure count on success
            cache.set(self.cache_key, {
                'state': 'closed',
                'failure_count': 0,
                'last_failure_time': None
            }, self.timeout * 2)
    
    def _on_failure(self):
        """Handle failed call."""
        cached_data = cache.get(self.cache_key) or {
            'state': 'closed',
            'failure_count': 0,
            'last_failure_time': None
        }
        
        cached_data['failure_count'] += 1
        cached_data['last_failure_time'] = timezone.now().isoformat()
        
        if cached_data['failure_count'] >= self.threshold:
            cached_data['state'] = 'open'
            self._update_health_record('open')
        elif cached_data['state'] == 'half_open':
            cached_data['state'] = 'open'
            self._update_health_record('open')
        
        cache.set(self.cache_key, cached_data, self.timeout * 2)
    
    def _update_health_record(self, circuit_state):
        """Update integration health record."""
        try:
            from .models import IntegrationProvider
            provider = IntegrationProvider.objects.filter(name=self.provider_name).first()
            if provider:
                health, created = IntegrationHealth.objects.get_or_create(
                    provider=provider,
                    defaults={
                        'is_healthy': circuit_state == 'closed',
                        'circuit_breaker_state': circuit_state,
                        'consecutive_failures': self.failure_count,
                    }
                )
                
                if not created:
                    health.is_healthy = circuit_state == 'closed'
                    health.circuit_breaker_state = circuit_state
                    health.consecutive_failures = self.failure_count
                    health.last_check_at = timezone.now()
                    health.save()
        except Exception as e:
            logger.error(f"Error updating health record: {e}")
    
    def force_open(self):
        """Force circuit breaker to open state."""
        cache.set(self.cache_key, {
            'state': 'open',
            'failure_count': self.threshold,
            'last_failure_time': timezone.now().isoformat()
        }, self.timeout * 2)
        self._update_health_record('open')
    
    def force_close(self):
        """Force circuit breaker to closed state."""
        cache.delete(self.cache_key)
        self._update_health_record('closed')
    
    def get_status(self):
        """Get detailed circuit breaker status."""
        return {
            'provider_name': self.provider_name,
            'state': self.state,
            'failure_count': self.failure_count,
            'last_failure_time': self.last_failure_time,
            'threshold': self.threshold,
            'timeout': self.timeout,
        }


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class CircuitBreakerDecorator:
    """Decorator for applying circuit breaker to functions."""
    
    def __init__(self, provider_name, threshold=5, timeout=60):
        self.circuit_breaker = CircuitBreaker(provider_name, threshold, timeout)
    
    def __call__(self, func):
        def wrapper(*args, **kwargs):
            return self.circuit_breaker.call(func, *args, **kwargs)
        return wrapper


# Convenience decorator
def circuit_breaker(provider_name, threshold=5, timeout=60):
    """Decorator for applying circuit breaker to functions."""
    return CircuitBreakerDecorator(provider_name, threshold, timeout)
