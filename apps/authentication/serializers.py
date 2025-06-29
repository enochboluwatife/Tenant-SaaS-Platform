from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from apps.tenants.models import TenantUser, Tenant


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT token serializer with additional user data."""
    
    def validate(self, attrs):
        """Validate credentials and return token with user info."""
        data = super().validate(attrs)
        
        # Add user information to token response
        user = self.user
        data['user'] = {
            'id': str(user.id),
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'tenant': {
                'id': str(user.tenant.id),
                'name': user.tenant.name,
                'domain': user.tenant.domain,
            } if user.tenant else None,
        }
        
        return data


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        """Validate login credentials."""
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials.')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.')
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Must include email and password.')


class RegisterSerializer(serializers.Serializer):
    """Serializer for user registration."""
    
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    first_name = serializers.CharField(max_length=30)
    last_name = serializers.CharField(max_length=30)
    tenant_name = serializers.CharField(max_length=255)
    tenant_domain = serializers.CharField(max_length=255)
    
    def validate(self, attrs):
        """Validate registration data."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match.")
        
        if TenantUser.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        
        if Tenant.objects.filter(domain=attrs['tenant_domain']).exists():
            raise serializers.ValidationError("A tenant with this domain already exists.")
        
        return attrs
    
    def create(self, validated_data):
        """Create tenant and user."""
        # Create tenant first
        tenant = Tenant.objects.create(
            name=validated_data['tenant_name'],
            domain=validated_data['tenant_domain'],
        )
        
        # Create user
        user = TenantUser.objects.create_user(
            email=validated_data['email'],
            username=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            tenant=tenant,
        )
        
        return user


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change."""
    
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        """Validate password change data."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New passwords don't match.")
        
        user = self.context['request'].user
        if not user.check_password(attrs['old_password']):
            raise serializers.ValidationError("Current password is incorrect.")
        
        return attrs
    
    def save(self):
        """Change the user's password."""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class PasswordResetSerializer(serializers.Serializer):
    """Serializer for password reset request."""
    
    email = serializers.EmailField()
    
    def validate_email(self, value):
        """Validate email exists."""
        if not TenantUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("No user found with this email address.")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation."""
    
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        """Validate password reset data."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("Passwords don't match.")
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile updates."""
    
    tenant_name = serializers.ReadOnlyField(source='tenant.name')
    
    class Meta:
        model = TenantUser
        fields = [
            'id', 'email', 'first_name', 'last_name', 'department', 
            'title', 'tenant_name', 'created_at', 'last_login'
        ]
        read_only_fields = ['id', 'email', 'tenant_name', 'created_at', 'last_login']
