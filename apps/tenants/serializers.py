from rest_framework import serializers
from .models import Tenant, TenantUser


class TenantSerializer(serializers.ModelSerializer):
    """Serializer for Tenant model."""
    
    subscription_status = serializers.ReadOnlyField()
    user_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Tenant
        fields = [
            'id', 'name', 'domain', 'plan', 'employee_count', 
            'sso_config', 'subscription_status', 'user_count',
            'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'subscription_status', 'user_count']
    
    def get_user_count(self, obj):
        """Get the number of users for this tenant."""
        return obj.users.count()
    
    def validate_domain(self, value):
        """Validate domain uniqueness."""
        if Tenant.objects.filter(domain=value).exists():
            raise serializers.ValidationError("A tenant with this domain already exists.")
        return value


class TenantUserSerializer(serializers.ModelSerializer):
    """Serializer for TenantUser model."""
    
    tenant_name = serializers.ReadOnlyField(source='tenant.name')
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = TenantUser
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 'full_name',
            'department', 'title', 'tenant', 'tenant_name', 'sso_attributes',
            'is_active', 'created_at', 'updated_at', 'last_login'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_login', 'tenant_name']
        extra_kwargs = {
            'password': {'write_only': True},
            'tenant': {'write_only': True}
        }
    
    def get_full_name(self, obj):
        """Get the full name of the user."""
        return f"{obj.first_name} {obj.last_name}".strip()
    
    def create(self, validated_data):
        """Create a new user with proper password handling."""
        password = validated_data.pop('password', None)
        user = TenantUser(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user
    
    def update(self, instance, validated_data):
        """Update user with proper password handling."""
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class TenantUserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new tenant users."""
    
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = TenantUser
        fields = [
            'email', 'username', 'first_name', 'last_name', 'department', 
            'title', 'password', 'password_confirm'
        ]
    
    def validate(self, attrs):
        """Validate password confirmation."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match.")
        return attrs
    
    def create(self, validated_data):
        """Create user with tenant from request context."""
        validated_data.pop('password_confirm')
        validated_data['tenant'] = self.context['request'].tenant
        return super().create(validated_data)


class TenantSummarySerializer(serializers.ModelSerializer):
    """Lightweight serializer for tenant summary information."""
    
    user_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Tenant
        fields = ['id', 'name', 'domain', 'plan', 'user_count', 'is_active']
    
    def get_user_count(self, obj):
        return obj.users.count()
