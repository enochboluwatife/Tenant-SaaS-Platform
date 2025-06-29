from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone


class CustomRefreshToken(RefreshToken):
    """Custom refresh token with additional claims."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_exp(lifetime=timezone.timedelta(days=7))
    
    @classmethod
    def for_user(cls, user):
        """Create a refresh token for a user."""
        token = cls()
        token['user_id'] = str(user.id)
        token['email'] = user.email
        if hasattr(user, 'tenant'):
            token['tenant_id'] = str(user.tenant.id)
            token['tenant_name'] = user.tenant.name
        return token
