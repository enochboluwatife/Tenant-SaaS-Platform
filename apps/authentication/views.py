from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login, logout
from django.utils import timezone
from .serializers import (
    CustomTokenObtainPairSerializer, LoginSerializer, RegisterSerializer,
    PasswordChangeSerializer, PasswordResetSerializer, PasswordResetConfirmSerializer,
    UserProfileSerializer
)
from apps.tenants.models import TenantUser
from apps.audit.models import AuditLog


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom JWT token view with additional user data."""
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        user = serializer.user  # This is the authenticated user
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            user.last_login = timezone.now()
            user.save()
            # Log the login
            AuditLog.log_action(
                user=user,
                tenant=user.tenant if hasattr(user, 'tenant') else None,
                action='LOGIN',
                resource_type='User',
                resource_id=str(user.id),
                request=request
            )
        return response


class CustomTokenRefreshView(TokenRefreshView):
    """Custom JWT refresh token view."""
    
    def post(self, request, *args, **kwargs):
        """Handle token refresh."""
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Log the token refresh
            AuditLog.log_action(
                user=request.user if request.user.is_authenticated else None,
                tenant=request.user.tenant if hasattr(request.user, 'tenant') else None,
                action='API_CALL',
                resource_type='Token',
                resource_id='refresh',
                request=request
            )
        
        return response


class LoginView(APIView):
    """Traditional login view with session authentication."""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Handle user login."""
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)
            
            # Update last login
            user.last_login = timezone.now()
            user.save()
            
            # Log the login
            AuditLog.log_action(
                user=user,
                tenant=user.tenant if hasattr(user, 'tenant') else None,
                action='LOGIN',
                resource_type='User',
                resource_id=str(user.id),
                request=request
            )
            
            return Response({
                'message': 'Login successful',
                'user': {
                    'id': str(user.id),
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'tenant': {
                        'id': str(user.tenant.id),
                        'name': user.tenant.name,
                        'domain': user.tenant.domain,
                    } if hasattr(user, 'tenant') and user.tenant else None,
                }
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """Logout view."""
    
    def post(self, request):
        """Handle user logout."""
        user = request.user
        
        # Log the logout
        AuditLog.log_action(
            user=user,
            tenant=user.tenant if hasattr(user, 'tenant') else None,
            action='LOGOUT',
            resource_type='User',
            resource_id=str(user.id),
            request=request
        )
        
        logout(request)
        return Response({'message': 'Logout successful'})


class RegisterView(APIView):
    """User registration view."""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Handle user registration."""
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Log the registration
            AuditLog.log_action(
                user=user,
                tenant=user.tenant,
                action='CREATE',
                resource_type='User',
                resource_id=str(user.id),
                new_values={
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'tenant_name': user.tenant.name,
                    'tenant_domain': user.tenant.domain,
                },
                request=request
            )
            
            return Response({
                'message': 'Registration successful',
                'user': {
                    'id': str(user.id),
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'tenant': {
                        'id': str(user.tenant.id),
                        'name': user.tenant.name,
                        'domain': user.tenant.domain,
                    }
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordChangeView(APIView):
    """Password change view."""
    
    def post(self, request):
        """Handle password change."""
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.save()
            
            # Log the password change
            AuditLog.log_action(
                user=user,
                tenant=user.tenant if hasattr(user, 'tenant') else None,
                action='UPDATE',
                resource_type='User',
                resource_id=str(user.id),
                new_values={'password_changed': True},
                request=request
            )
            
            return Response({'message': 'Password changed successfully'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetView(APIView):
    """Password reset request view."""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Handle password reset request."""
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = TenantUser.objects.get(email=email)
            
            # Generate reset token (simplified - in production, use proper token generation)
            token = RefreshToken.for_user(user)
            
            # Log the password reset request
            AuditLog.log_action(
                user=user,
                tenant=user.tenant if hasattr(user, 'tenant') else None,
                action='API_CALL',
                resource_type='User',
                resource_id=str(user.id),
                new_values={'password_reset_requested': True},
                request=request
            )
            
            # In production, send email with reset link
            # For now, just return success
            return Response({
                'message': 'Password reset email sent',
                'token': str(token.access_token)  # In production, don't return token in response
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    """Password reset confirmation view."""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Handle password reset confirmation."""
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            # In production, validate the token properly
            # For now, just return success
            return Response({'message': 'Password reset successful'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    """User profile view."""
    
    def get(self, request):
        """Get current user's profile."""
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    def put(self, request):
        """Update current user's profile."""
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            old_values = {
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'department': request.user.department,
                'title': request.user.title,
            }
            
            user = serializer.save()
            
            # Log the profile update
            AuditLog.log_action(
                user=user,
                tenant=user.tenant if hasattr(user, 'tenant') else None,
                action='UPDATE',
                resource_type='User',
                resource_id=str(user.id),
                old_values=old_values,
                new_values={
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'department': user.department,
                    'title': user.title,
                },
                request=request
            )
            
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def revoke_token(request):
    """Revoke JWT token."""
    try:
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            # Log the token revocation
            AuditLog.log_action(
                user=request.user,
                tenant=request.user.tenant if hasattr(request.user, 'tenant') else None,
                action='API_CALL',
                resource_type='Token',
                resource_id='revoke',
                request=request
            )
            
            return Response({'message': 'Token revoked successfully'})
        else:
            return Response({'error': 'Refresh token required'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
