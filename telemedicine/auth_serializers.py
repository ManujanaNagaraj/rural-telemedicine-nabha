from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from telemedicine.models import Patient, Doctor


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom token serializer that includes user information.
    """
    def validate(self, attrs):
        data = super().validate(attrs)
        
        user = self.user
        data['user_id'] = user.id
        data['username'] = user.username
        data['email'] = user.email
        data['first_name'] = user.first_name
        data['last_name'] = user.last_name
        data['is_staff'] = user.is_staff
        
        # Add user type
        if hasattr(user, 'patient'):
            data['user_type'] = 'patient'
            data['profile_id'] = user.patient.id
        elif hasattr(user, 'doctor'):
            data['user_type'] = 'doctor'
            data['profile_id'] = user.doctor.id
        else:
            data['user_type'] = 'admin' if user.is_staff else 'user'
            data['profile_id'] = None
        
        return data


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login with username/email and password.
    """
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid username or password")
        
        if not user.check_password(password):
            raise serializers.ValidationError("Invalid username or password")
        
        attrs['user'] = user
        return attrs


class LogoutSerializer(serializers.Serializer):
    """
    Serializer for user logout with refresh token.
    """
    refresh = serializers.CharField(required=True)
    
    def validate_refresh(self, value):
        try:
            token = RefreshToken(value)
        except Exception:
            raise serializers.ValidationError("Invalid refresh token")
        return value


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user details.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff']
        read_only_fields = ['id', 'is_staff']


class PatientUserSerializer(serializers.ModelSerializer):
    """
    Serializer for patient user registration.
    """
    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'confirm_password']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password']
        )
        return user


class DoctorUserSerializer(serializers.ModelSerializer):
    """
    Serializer for doctor user registration.
    """
    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'confirm_password']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password']
        )
        return user


class TokenResponseSerializer(serializers.Serializer):
    """
    Serializer for token response.
    """
    access = serializers.CharField()
    refresh = serializers.CharField()
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField()
    user_type = serializers.CharField()
    profile_id = serializers.IntegerField(allow_null=True)
